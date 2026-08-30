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


from .models import Application, PersonalInfo, ContactAddress, AcademicInfo, GuardianInfo, AdditionalInfo
from .ai_models import validate_passport_image
from .forms import (
    AcademicInformationForm, AdditionalInformationForm, ContactAddressForm,
    DeclarationForm, GuardianInformationForm, PersonalInformationForm
)
from .ai_models import validate_passport_image
from .forms import (
    AcademicInformationForm,
    AdditionalInformationForm,
    ContactAddressForm,
    DeclarationForm,
    GuardianInformationForm,
    PersonalInformationForm,
)
from .models import (
    AcademicInfo,
    AdditionalInfo,
    Application,
    ContactAddress,
    GuardianInfo,
    PersonalInfo,
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
        {"label": label, "done": i < current_index, "current": i == current_index}
        for i, label in enumerate(STATUS_TIMELINE_STEPS)
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_or_create_application(user):
    """Return first application for user, creating one if absent."""
    app = Application.objects.filter(applicant=user).first()
    if not app:
        app = Application.objects.create(applicant=user)
    return app


@login_required
def step_personal_information(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    personal_info, _ = PersonalInfo.objects.get_or_create(application=application)
    return _step_personal(request, application, personal_info, PersonalInformationForm, "step_contact_address", "Personal Information", "Upload a passport-size student photo. JPG, PNG, or PDF files are accepted.")


@login_required
@require_POST
def validate_photo_api(request):
    try:
        data_url = request.POST.get("image") or request.body and _extract_json_image(request)
        if not data_url:
            return JsonResponse({"valid": False, "message": "No image received"}, status=400)

        if "," in data_url:
            _header, encoded = data_url.split(",", 1)
        else:
            encoded = data_url

        image_bytes = base64.b64decode(encoded)
        is_valid, message = validate_passport_image(image_bytes)
        return JsonResponse({"valid": is_valid, "message": message})
    except Exception as error:
        return JsonResponse({"valid": False, "message": f"Validation error: {str(error)}"}, status=500)


def _extract_json_image(request):
    import json

    try:
        body = json.loads(request.body)
        return body.get("image")
    except Exception:
        return None


@login_required
def step_contact_address(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    contact_address, _ = ContactAddress.objects.get_or_create(application=application)
    return _step(request, contact_address, ContactAddressForm, "contact_address_status", "step_guardian_information", "Contact & Address", "Enter a current contact number and full address.")


@login_required
def step_academic_information(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    academic_info, _ = AcademicInfo.objects.get_or_create(application=application)
    return _step(request, academic_info, AcademicInformationForm, "academic_info_status", "step_additional_information", "Academic Information", "Intermediate fields are required unless you select Result: Awaited.")


@login_required
def step_guardian_information(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    guardian_info, _ = GuardianInfo.objects.get_or_create(application=application)
    return _step(request, guardian_info, GuardianInformationForm, "guardian_info_status", "step_academic_information", "Guardian & Emergency Contact", "Provide a guardian and an emergency contact who can be reached.")


@login_required
def step_additional_information(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    additional_info, _ = AdditionalInfo.objects.get_or_create(application=application)
    return _step(request, additional_info, AdditionalInformationForm, "additional_info_status", "documents", "Additional Information", "Answer each requirement so Admissions can make suitable arrangements.")


def _step_personal(request, application, section_obj, form_class, next_route, title, guidance):
    """Handler for PersonalInfo section with photo upload."""
    form = form_class(request.POST or None, request.FILES or None, instance=section_obj)

def _compress_image(uploaded_file, max_dim=600):
    """
    Resize image so longest side ≤ max_dim and JPEG-compress it.
    Returns (base64_string, content_type).
    """
    uploaded_file.seek(0)
    img = Image.open(uploaded_file).convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return encoded, "image/jpeg"


# ---------------------------------------------------------------------------
# Generic step handler — works with per-section sub-models
# ---------------------------------------------------------------------------
SECTION_MODEL_MAP = {
    "personal_info_status": (PersonalInfo, "personal_info"),
    "contact_address_status": (ContactAddress, "contact_address"),
    "academic_info_status": (AcademicInfo, "academic_info"),
    "guardian_info_status": (GuardianInfo, "guardian_info"),
    "additional_info_status": (AdditionalInfo, "additional_info"),
}


def _step(request, application, form_class, status_field, next_route, title, guidance):
    SectionModel, related_name = SECTION_MODEL_MAP[status_field]
    section, _ = SectionModel.objects.get_or_create(application=application)
    form = form_class(
        request.POST or None, request.FILES or None, instance=section
    )

    if request.method == "POST" and form.is_valid():
        uploaded_photo = request.FILES.get("student_photo")

        if uploaded_photo:
            uploaded_photo.seek(0)
            # AI validation

            is_valid, error_message = validate_passport_image(uploaded_photo)
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
            # Compress + encode after AI validation passes
            encoded, content_type = _compress_image(uploaded_photo)
            section_obj = form.save(commit=False)
            section_obj.student_photo = encoded
            section_obj.student_photo_type = content_type
        else:
            section_obj = form.save(commit=False)

            # Reset after AI validation so the complete file can be read
            uploaded_photo.seek(0)

        updated = form.save(commit=False)

        if uploaded_photo:
            # Convert ONLY after the AI check passes
            updated.student_photo = base64.b64encode(
                uploaded_photo.read()
            ).decode("ascii")
            updated.student_photo_type = (
                uploaded_photo.content_type or "image/jpeg"
            )

        updated.status = "completed"
        updated.save()

        setattr(section_obj, status_field, "completed")
        section_obj.save()

        if status_field == "academic_info_status":
            from documents.helpers import update_documents_status
            update_documents_status(application)

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


def _step(request, section_obj, form_class, status_field, next_route, title, guidance):
    """Generic handler for non-photo form sections."""
    form = form_class(request.POST or None, instance=section_obj)

    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.status = "completed"
        updated.save()

        # Update documents status if academic info was completed
        if status_field == "academic_info_status":
            from documents.views import update_documents_status
            update_documents_status(section_obj.application)

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
        },)
# ---------------------------------------------------------------------------
# Rate-limited photo validation API (max 5 calls/min per user)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def validate_photo_api(request):
    cache_key = f"photo_ratelimit_{request.user.pk}"
    calls = cache.get(cache_key, 0)
    if calls >= 5:
        return JsonResponse(
            {"valid": False, "message": "Too many validation attempts. Please wait a moment."},
            status=429,
        )
    cache.set(cache_key, calls + 1, timeout=60)

    try:
        data_url = request.POST.get("image")
        if not data_url:
            body = json.loads(request.body or "{}")
            data_url = body.get("image", "")
        if not data_url:
            return JsonResponse({"valid": False, "message": "No image received"}, status=400)

        header, _, encoded = data_url.partition(",")
        image_bytes = base64.b64decode(encoded or data_url)
        is_valid, message = validate_passport_image(image_bytes)
        return JsonResponse({"valid": is_valid, "message": message})
    except Exception as error:
        return JsonResponse({"valid": False, "message": f"Validation error: {str(error)}"}, status=500)


# ---------------------------------------------------------------------------
# Step views
# ---------------------------------------------------------------------------
@login_required
def my_application(request):
    application = _get_or_create_application(request.user)
    return render(request, "applications/overview.html", {
        "active_nav": "application",
        "checklist": application.checklist,
        "progress_percent": application.progress_percent,
        "is_ready_for_submission": application.is_ready_for_submission,
    })


@login_required
def step_personal_information(request):
    application = _get_or_create_application(request.user)
    return _step(
        request, application, PersonalInformationForm,
        "personal_info_status", "step_contact_address",
        "Personal Information",
        "Upload a passport-size student photo. JPG or PNG files are accepted.",
    )


@login_required
def step_contact_address(request):
    application = _get_or_create_application(request.user)
    return _step(
        request, application, ContactAddressForm,
        "contact_address_status", "step_guardian_information",
        "Contact & Address",
        "Enter a current contact number and full mailing address.",
    )


@login_required
def step_guardian_information(request):
    application = _get_or_create_application(request.user)
    return _step(
        request, application, GuardianInformationForm,
        "guardian_info_status", "step_academic_information",
        "Guardian & Emergency Contact",
        "Provide a guardian and an emergency contact who can be reached promptly.",
    )


@login_required
def step_academic_information(request):
    application = _get_or_create_application(request.user)
    return _step(
        request, application, AcademicInformationForm,
        "academic_info_status", "step_additional_information",
        "Academic Information",
        "Intermediate fields are required unless you select Result Awaited.",
    )


@login_required
def step_additional_information(request):
    application = _get_or_create_application(request.user)
    return _step(
        request, application, AdditionalInformationForm,
        "additional_info_status", "documents",
        "Additional Information",
        "Answer each question so Admissions can make suitable arrangements.",
    )


@login_required
def declaration(request):
    """Legacy URL — redirect to documents page where declaration is now embedded."""
    return redirect("documents")


@login_required
def review_application(request):
    application = _get_or_create_application(request.user)
    return render(request, "applications/review.html", {
        "active_nav": "application",
        "application": application,
    })


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
        return render(request, "applications/submit.html", {
            "active_nav": "application",
            "application": application,
            "submitted": True,
        })
    return redirect("review_application")


@login_required
def reset_application(request):
    application = _get_or_create_application(request.user)
    if request.method == "POST":
        # Reset all section statuses
        PersonalInfo.objects.filter(application=application).update(status="not_started")
        ContactAddress.objects.filter(application=application).update(status="not_started")
        AcademicInfo.objects.filter(application=application).update(status="not_started")
        GuardianInfo.objects.filter(application=application).update(status="not_started")
        AdditionalInfo.objects.filter(application=application).update(status="not_started")
        
        # Reset application status
        for model_cls, related_name in SECTION_MODEL_MAP.values():
            section = getattr(application, related_name, None)
            if section:
                status_field = next(
                    k for k, (m, r) in SECTION_MODEL_MAP.items() if r == related_name
                )
                setattr(section, status_field, "not_started")
                section.save(update_fields=[status_field])
        from documents.helpers import update_documents_status
        from applications.models import DocumentsSummary
        summary = getattr(application, "documents_summary", None)
        if summary:
            summary.documents_status = "not_started"
            summary.save()
        application.status = "draft"
        application.declaration_accepted = False
        application.save()
    return redirect("my_application")


@login_required
def application_status(request):
    application = _get_or_create_application(request.user)
    return render(request, "applications/status.html", {
        "active_nav": "status",
        "application": application,
        "status_timeline": _build_timeline(application),
    })
