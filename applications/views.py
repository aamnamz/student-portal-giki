import base64
import io
import json

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from PIL import Image

from .ai_models import validate_passport_image
from .forms import (
    AcademicInformationForm,
    AdmissionSchemeForm,
    AdmissionTestForm,
    ContactAddressForm,
    CurrentEmploymentForm,
    DeclarationForm,
    FormSubmissionForm,
    PersonalInformationForm,
    ProgramPreferenceForm,
)
from .models import (
    AcademicInfo,
    AdmissionScheme,
    AdmissionTest,
    Application,
    ContactAddress,
    CurrentEmployment,
    FormSubmission,
    PersonalInfo,
    ProgramPreference,
)


# ---------------------------------------------------------------------------
# Status timeline
# ---------------------------------------------------------------------------
STATUS_TIMELINE_STEPS = [
    "Registration",
    "Application Started",
    "Application Completed",
    "Submitted",
    "Under Review",
    "Decision",
]

STATUS_TO_STEP_INDEX = {
    "draft": 1,
    "ready": 2,
    "submitted": 3,
    "under_review": 4,
    "action_required": 4,
    "accepted": 5,
    "rejected": 5,
}


def _build_timeline(application):
    current_index = STATUS_TO_STEP_INDEX.get(application.status, 0)

    return [
        {
            "label": label,
            "done": i < current_index,
            "current": i == current_index,
        }
        for i, label in enumerate(STATUS_TIMELINE_STEPS)
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_or_create_application(user):
    """Return the user's application, creating one if absent."""
    app = Application.objects.filter(applicant=user).first()

    if not app:
        app = Application.objects.create(applicant=user)

    return app


def _get_or_build(model, application):
    """
    Return the application's existing section row, or an UNSAVED instance
    if none exists yet.
    """
    try:
        return model.objects.get(application=application)
    except model.DoesNotExist:
        return model(application=application)


def _extract_json_image(request):
    try:
        body = json.loads(request.body)
        return body.get("image")
    except Exception:
        return None


def _compress_image(uploaded_file, max_dim=600):
    """
    Resize image so longest side <= max_dim and JPEG-compress it.
    Returns (base64_string, content_type).
    """
    uploaded_file.seek(0)

    img = Image.open(uploaded_file).convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)

    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    return encoded, "image/jpeg"


def _encode_file(uploaded_file):
    """
    Base64-encode an uploaded file as-is.
    Returns (base64_string, content_type).
    """
    uploaded_file.seek(0)

    encoded = base64.b64encode(uploaded_file.read()).decode("ascii")
    content_type = uploaded_file.content_type or "application/octet-stream"

    return encoded, content_type


# ---------------------------------------------------------------------------
# Application overview
# ---------------------------------------------------------------------------
@login_required
def my_application(request):
    application = _get_or_create_application(request.user)

    return render(
        request,
        "applications/overview.html",
        {
            "active_nav": "application",
            "checklist": application.checklist,
            "progress_percent": application.progress_percent,
            "is_ready_for_submission": application.is_ready_for_submission,
        },
    )


# ---------------------------------------------------------------------------
# Personal Information — Step 1
# ---------------------------------------------------------------------------
@login_required
def step_personal_information(request):
    application = _get_or_create_application(request.user)

    personal_info = _get_or_build(PersonalInfo, application)

    return _step_personal(
        request,
        application,
        personal_info,
        PersonalInformationForm,
        "step_contact_address",
        "Personal Information",
        "Upload a passport-size student photo. JPG or PNG files are accepted.",
    )


def _step_personal(
    request,
    application,
    section_obj,
    form_class,
    next_route,
    title,
    guidance,
):
    """Handler for PersonalInfo section with photo upload."""

    form = form_class(
        request.POST or None,
        request.FILES or None,
        instance=section_obj,
    )

    if request.method == "POST" and form.is_valid():
        uploaded_photo = request.FILES.get("student_photo")

        if uploaded_photo:
            uploaded_photo.seek(0)

            is_valid, error_message = validate_passport_image(
                uploaded_photo
            )

            if not is_valid:
                form.add_error("student_photo", error_message)

                return render(
                    request,
                    "applications/step_form.html",
                    {
                        "active_nav": "application",
                        "application": application,
                        "form": form,
                        "title": title,
                        "guidance": guidance,
                    },
                )

            encoded, content_type = _compress_image(uploaded_photo)

            updated = form.save(commit=False)
            updated.student_photo = encoded
            updated.student_photo_type = content_type

        else:
            updated = form.save(commit=False)

        updated.status = "completed"
        updated.save()

        application.updated_at = timezone.now()
        application.save(update_fields=["updated_at"])

        return redirect(next_route)

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": title,
            "guidance": guidance,
        },
    )


# ---------------------------------------------------------------------------
# Photo validation API
# ---------------------------------------------------------------------------
@login_required
@require_POST
def validate_photo_api(request):
    cache_key = f"photo_ratelimit_{request.user.pk}"

    calls = cache.get(cache_key, 0)

    if calls >= 5:
        return JsonResponse(
            {
                "valid": False,
                "message": "Too many validation attempts. Please wait a moment.",
            },
            status=429,
        )

    cache.set(cache_key, calls + 1, timeout=60)

    try:
        data_url = request.POST.get("image")

        if not data_url:
            data_url = _extract_json_image(request)

        if not data_url:
            return JsonResponse(
                {
                    "valid": False,
                    "message": "No image received",
                },
                status=400,
            )

        _header, _, encoded = data_url.partition(",")

        image_bytes = base64.b64decode(encoded or data_url)

        is_valid, message = validate_passport_image(image_bytes)

        return JsonResponse(
            {
                "valid": is_valid,
                "message": message,
            }
        )

    except Exception as error:
        return JsonResponse(
            {
                "valid": False,
                "message": f"Validation error: {str(error)}",
            },
            status=500,
        )


# ---------------------------------------------------------------------------
# Section model mapping
# ---------------------------------------------------------------------------
SECTION_MODEL_MAP = {
    "personal_info_status": (PersonalInfo, "personal_info"),
    "contact_address_status": (ContactAddress, "contact_address"),
    "academic_info_status": (AcademicInfo, "academic_info"),
    "program_preference_status": (
        ProgramPreference,
        "program_preference",
    ),
    "admission_test_status": (AdmissionTest, "admission_test"),
    "admission_scheme_status": (
        AdmissionScheme,
        "admission_scheme",
    ),
    "employment_status": (
        CurrentEmployment,
        "current_employment",
    ),
    "form_submission_status": (
        FormSubmission,
        "form_submission",
    ),
}


# ---------------------------------------------------------------------------
# Generic step handler
# ---------------------------------------------------------------------------
def _step(
    request,
    section_obj,
    form_class,
    status_field,
    next_route,
    title,
    guidance,
):
    """Generic handler for non-file form sections."""

    form = form_class(
        request.POST or None,
        instance=section_obj,
    )

    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)

        updated.status = "completed"
        updated.save()

        return redirect(next_route)

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": section_obj.application,
            "form": form,
            "title": title,
            "guidance": guidance,
        },
    )


# ---------------------------------------------------------------------------
# Step 2 — Contact & Address
# ---------------------------------------------------------------------------
@login_required
def step_contact_address(request):
    application = _get_or_create_application(request.user)

    contact_address = _get_or_build(ContactAddress, application)

    return _step(
        request,
        contact_address,
        ContactAddressForm,
        "contact_address_status",
        "step_academic_information",
        "Contact & Address",
        "Enter a current contact number and full address.",
    )


# ---------------------------------------------------------------------------
# Step 3 — Academic Information
# ---------------------------------------------------------------------------
@login_required
def step_academic_information(request):
    application = _get_or_create_application(request.user)

    academic_info = _get_or_build(AcademicInfo, application)

    return _step(
        request,
        academic_info,
        AcademicInformationForm,
        "academic_info_status",
        "step_program_preference",
        "Academic Information",
        "Enter your previous academic information.",
    )


# ---------------------------------------------------------------------------
# Step 4 — Program Preferences
# ---------------------------------------------------------------------------
@login_required
def step_program_preference(request):
    application = _get_or_create_application(request.user)

    program_preference = _get_or_build(
        ProgramPreference,
        application,
    )

    return _step(
        request,
        program_preference,
        ProgramPreferenceForm,
        "program_preference_status",
        "step_admission_test",
        "Program Preferences",
        "Choose the program you're applying for.",
    )


# ---------------------------------------------------------------------------
# Step 5 — Admission Test
# ---------------------------------------------------------------------------
@login_required
def step_admission_test(request):
    application = _get_or_create_application(request.user)

    admission_test = _get_or_build(
        AdmissionTest,
        application,
    )

    title = "Admission Test"
    guidance = (
        "If you've already qualified an entrance test, upload evidence "
        "of your result."
    )

    form = AdmissionTestForm(
        request.POST or None,
        request.FILES or None,
        instance=admission_test,
    )

    if request.method == "POST" and form.is_valid():
        uploaded_evidence = request.FILES.get("evidence_document")

        updated = form.save(commit=False)

        if uploaded_evidence:
            encoded, content_type = _encode_file(uploaded_evidence)
            updated.evidence_document = encoded
            updated.evidence_document_type = content_type

        updated.status = "completed"
        updated.save()

        application.updated_at = timezone.now()
        application.save(update_fields=["updated_at"])

        return redirect("step_admission_scheme")

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": title,
            "guidance": guidance,
        },
    )


# ---------------------------------------------------------------------------
# Step 6 — Admission Scheme
# ---------------------------------------------------------------------------
@login_required
def step_admission_scheme(request):
    application = _get_or_create_application(request.user)

    admission_scheme = _get_or_build(
        AdmissionScheme,
        application,
    )

    return _step(
        request,
        admission_scheme,
        AdmissionSchemeForm,
        "admission_scheme_status",
        "step_employment",
        "Admission Scheme",
        "Let us know which admission scheme applies to you.",
    )


# ---------------------------------------------------------------------------
# Step 7 — Current Employment
# ---------------------------------------------------------------------------
@login_required
def step_employment(request):
    application = _get_or_create_application(request.user)

    current_employment = _get_or_build(
        CurrentEmployment,
        application,
    )

    return _step(
        request,
        current_employment,
        CurrentEmploymentForm,
        "employment_status",
        "form_submission",
        "Current Employment",
        "Tell us about your current employment, if any.",
    )


# ---------------------------------------------------------------------------
# Step 8 — Form Submission
# ---------------------------------------------------------------------------
@login_required
def form_submission(request):
    application = _get_or_create_application(request.user)

    form_submission_obj = _get_or_build(
        FormSubmission,
        application,
    )

    form = FormSubmissionForm(
        request.POST or None,
        instance=form_submission_obj,
    )

    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.status = "completed"
        updated.save()

        application.updated_at = timezone.now()
        application.save(update_fields=["updated_at"])

        return redirect("declaration")

    return render(
        request,
        "applications/form_submission.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "checklist": application.checklist,
            "progress_percent": application.progress_percent,
            "is_ready_for_submission": application.is_ready_for_submission,
        },
    )


# ---------------------------------------------------------------------------
# Declaration
# ---------------------------------------------------------------------------
@login_required
def declaration(request):
    application = _get_or_create_application(request.user)

    form = DeclarationForm(
        request.POST or None,
        instance=application,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect("review_application")

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": "Declaration",
            "guidance": (
                "Please review and accept the declaration to "
                "continue to your application review."
            ),
        },
    )


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------
@login_required
def review_application(request):
    application = _get_or_create_application(request.user)

    return render(
        request,
        "applications/review.html",
        {
            "active_nav": "application",
            "application": application,
        },
    )


# ---------------------------------------------------------------------------
# Submit Application
# ---------------------------------------------------------------------------
@login_required
def submit_application(request):
    application = _get_or_create_application(request.user)

    if (
        request.method == "POST"
        and application.is_ready_for_submission
        and application.declaration_accepted
    ):
        application.status = "submitted"
        application.submitted_at = timezone.now()
        application.save()

        return render(
            request,
            "applications/submit.html",
            {
                "active_nav": "application",
                "application": application,
                "submitted": True,
            },
        )

    return redirect("review_application")


# ---------------------------------------------------------------------------
# Reset Application
# ---------------------------------------------------------------------------
@login_required
def reset_application(request):
    application = _get_or_create_application(request.user)

    if request.method == "POST":
        PersonalInfo.objects.filter(
            application=application
        ).update(status="not_started")

        ContactAddress.objects.filter(
            application=application
        ).update(status="not_started")

        AcademicInfo.objects.filter(
            application=application
        ).update(status="not_started")

        ProgramPreference.objects.filter(
            application=application
        ).update(status="not_started")

        AdmissionTest.objects.filter(
            application=application
        ).update(status="not_started")

        AdmissionScheme.objects.filter(
            application=application
        ).update(status="not_started")

        CurrentEmployment.objects.filter(
            application=application
        ).update(status="not_started")

        FormSubmission.objects.filter(
            application=application
        ).update(status="not_started")

        application.status = "draft"
        application.declaration_accepted = False
        application.submitted_at = None
        application.save()

    return redirect("my_application")


# ---------------------------------------------------------------------------
# Application Status
# ---------------------------------------------------------------------------
@login_required
def application_status(request):
    application = _get_or_create_application(request.user)

    return render(
        request,
        "applications/status.html",
        {
            "active_nav": "status",
            "application": application,
            "status_timeline": _build_timeline(application),
        },
    )
