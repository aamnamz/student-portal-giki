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

from dashboard.models import notify

from .ai_models import validate_passport_image
from .forms import (
    AcademicInformationForm,
    AdmissionSchemeForm,
    AdmissionTestForm,
    ApplicationFormForm,
    ContactAddressForm,
    CurrentEmploymentForm,
    DeclarationForm,
    PersonalInformationForm,
    ProcessingFeeForm,
    ProgramPreferenceForm,
    RefereeInformationForm,
    TestCenterForm,
)
from .models import (
    AcademicInfo,
    AdmissionScheme,
    AdmissionTest,
    Application,
    ApplicationForm,
    ContactAddress,
    CurrentEmployment,
    PersonalInfo,
    ProcessingFee,
    ProgramPreference,
    RefereeInformation,
    TestCenter,
)


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


STEP_ROUTE_ORDER = [
    ("personal_info_status", "step_personal_information"),
    ("contact_address_status", "step_contact_address"),
    ("academic_info_status", "step_academic_information"),
    ("program_preference_status", "step_program_preference"),
    ("admission_test_status", "step_admission_test"),
    ("admission_scheme_status", "step_admission_scheme"),
    ("employment_status", "step_employment"),
    ("form_submission_status", "form_submission"),
]


SECTION_MODEL_MAP = {
    "personal_info_status": (PersonalInfo, "personal_info"),
    "contact_address_status": (ContactAddress, "contact_address"),
    "academic_info_status": (AcademicInfo, "academic_info"),
    "program_preference_status": (ProgramPreference, "program_preference"),
    "admission_test_status": (AdmissionTest, "admission_test"),
    "admission_scheme_status": (AdmissionScheme, "admission_scheme"),
    "employment_status": (CurrentEmployment, "current_employment"),
    "processing_fee_status": (ProcessingFee, "processing_fee"),
    "referee_information_status": (RefereeInformation, "referee_information"),
    "test_center_status": (TestCenter, "test_center"),
    "application_form_status": (ApplicationForm, "application_form"),
}


def _get_or_create_application(user):
    """Return the user's application, creating one if absent."""
    application = Application.objects.filter(applicant=user).first()

    if not application:
        application = Application.objects.create(applicant=user)

    return application


def _get_or_build(model, application):
    """Return the existing section object or an unsaved instance."""
    try:
        return model.objects.get(application=application)
    except model.DoesNotExist:
        return model(application=application)


def _build_timeline(application):
    current_index = STATUS_TO_STEP_INDEX.get(application.status, 0)

    return [
        {
            "label": label,
            "done": index < current_index,
            "current": index == current_index,
        }
        for index, label in enumerate(STATUS_TIMELINE_STEPS)
    ]


def _guidance(title, items):
    return {
        "title": title,
        "items": items,
    }


def _extract_json_image(request):
    try:
        body = json.loads(request.body)
        return body.get("image")
    except Exception:
        return None


def _compress_image(uploaded_file, max_dim=600):
    """Resize and JPEG-compress an uploaded image."""
    uploaded_file.seek(0)

    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail((max_dim, max_dim), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(
        buffer,
        format="JPEG",
        quality=85,
        optimize=True,
    )

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    return encoded, "image/jpeg"


def _encode_file(uploaded_file):
    """Base64-encode an uploaded file."""
    uploaded_file.seek(0)

    encoded = base64.b64encode(uploaded_file.read()).decode("ascii")
    content_type = uploaded_file.content_type or "application/octet-stream"

    return encoded, content_type


@login_required
def continue_application(request):
    application = _get_or_create_application(request.user)

    for status_field, route_name in STEP_ROUTE_ORDER:
        if getattr(application, status_field) != "completed":
            return redirect(route_name)

    return redirect("declaration")


@login_required
def step_personal_information(request):
    application = _get_or_create_application(request.user)
    personal_info = _get_or_build(PersonalInfo, application)

    guidance = (
        "Make sure your personal details match your official records and "
        "review them carefully before continuing."
    )

    step_guidance = _guidance(
        "Personal Information",
        [
            "Enter your details exactly as shown on your official records.",
            "Complete all required fields.",
            "Review your information carefully before continuing.",
        ],
    )

    return _step_personal(
        request,
        application,
        personal_info,
        PersonalInformationForm,
        "step_contact_address",
        "Personal Information",
        guidance,
        step_guidance,
    )


def _step_personal(
    request,
    application,
    section_obj,
    form_class,
    next_route,
    title,
    guidance,
    step_guidance,
):
    locked = application.section_i_locked

    form = form_class(
        request.POST or None,
        request.FILES or None,
        instance=section_obj,
    )

    if not locked and request.method == "POST":
        uploaded_photo = request.FILES.get("student_photo")
        is_valid = False

        if uploaded_photo:
            uploaded_photo.seek(0)

            is_valid, error_message = validate_passport_image(
                uploaded_photo
            )

            if not is_valid:
                form.add_error("student_photo", error_message)
            else:
                encoded, content_type = _compress_image(uploaded_photo)

                section_obj.student_photo = encoded
                section_obj.student_photo_type = content_type

                form.fields["student_photo"].required = False

                if "student_photo" in form.files:
                    form.files = form.files.copy()
                    form.files.pop("student_photo", None)

        if form.is_valid() and "student_photo" not in form.errors:
            updated = form.save(commit=False)

            if uploaded_photo and is_valid:
                updated.student_photo = section_obj.student_photo
                updated.student_photo_type = section_obj.student_photo_type

            updated.status = "completed"
            updated.save()

            application.updated_at = timezone.now()
            application.save(update_fields=["updated_at"])

            return redirect(next_route)

    if locked:
        for field in form.fields.values():
            field.disabled = True

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": title,
            "guidance": guidance,
            "step_guidance": step_guidance,
            "locked": locked,
            "lock_message": (
                "Your application has been submitted. Section I is now "
                "read-only."
            ),
        },
    )


@login_required
@require_POST
def validate_photo_api(request):
    cache_key = f"photo_ratelimit_{request.user.pk}"
    calls = cache.get(cache_key, 0)

    if calls >= 5:
        return JsonResponse(
            {
                "valid": False,
                "message": (
                    "Too many validation attempts. "
                    "Please wait a moment."
                ),
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


def _step(
    request,
    section_obj,
    form_class,
    status_field,
    next_route,
    title,
    guidance,
    step_guidance,
):
    application = section_obj.application
    locked = application.section_i_locked

    form = form_class(
        request.POST or None,
        instance=section_obj,
    )

    if not locked and request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.status = "completed"
        updated.save()

        return redirect(next_route)

    if locked:
        for field in form.fields.values():
            field.disabled = True

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": title,
            "guidance": guidance,
            "step_guidance": step_guidance,
            "locked": locked,
            "lock_message": (
                "Your application has been submitted. Section I is now "
                "read-only."
            ),
        },
    )


@login_required
def step_contact_address(request):
    application = _get_or_create_application(request.user)
    contact_address = _get_or_build(ContactAddress, application)

    guidance = (
        "Enter a complete and accurate address for correspondence. If your "
        "Mailing Address is the same as your Permanent Address, select Same "
        "as permanent address."
    )

    step_guidance = _guidance(
        "Contact & Addresses",
        [
            "Enter a complete and accurate correspondence address.",
            "Select “Same as permanent address” if both addresses are identical.",
            "Check your contact details before continuing.",
        ],
    )

    return _step(
        request,
        contact_address,
        ContactAddressForm,
        "contact_address_status",
        "step_academic_information",
        "Contact & Addresses",
        guidance,
        step_guidance,
    )


@login_required
def step_academic_information(request):
    application = _get_or_create_application(request.user)
    academic_info = _get_or_build(AcademicInfo, application)

    guidance = (
        "Complete all required fields using information from your official "
        "certificates or transcripts. If you have multiple certificates or "
        "degrees, enter each one separately."
    )

    step_guidance = _guidance(
        "Previous Education",
        [
            "Enter information from your official certificates or transcripts.",
            "Complete all required fields.",
            "Add each certificate or degree separately when applicable.",
        ],
    )

    return _step(
        request,
        academic_info,
        AcademicInformationForm,
        "academic_info_status",
        "step_program_preference",
        "Previous Education",
        guidance,
        step_guidance,
    )


@login_required
def step_program_preference(request):
    application = _get_or_create_application(request.user)
    program_preference = _get_or_build(
        ProgramPreference,
        application,
    )

    guidance = (
        "Review the available programs carefully and select the one you wish "
        "to pursue. Make sure you meet its eligibility requirements before "
        "continuing."
    )

    step_guidance = _guidance(
        "Program Selection",
        [
            "Review the available programs carefully.",
            "Select the program you wish to pursue.",
            "Make sure you meet the program’s eligibility requirements.",
        ],
    )

    return _step(
        request,
        program_preference,
        ProgramPreferenceForm,
        "program_preference_status",
        "step_admission_test",
        "Program Selection",
        guidance,
        step_guidance,
    )


@login_required
def step_admission_test(request):
    application = _get_or_create_application(request.user)
    locked = application.section_i_locked
    admission_test = _get_or_build(AdmissionTest, application)

    title = "Entry Test"

    guidance = (
        "Complete all required fields marked with * "
    )

    step_guidance = _guidance(
        "Entry Test",
        [
            "Complete all required fields marked with *.",
            "Candidates who have already qualified the ETS GRE General or HEC ETC HAT Test are exempted from the GIKI Admission Test.",
            "If you select “Already Qualified Entrance Test”, provide the required test details.",
            "Upload the required supporting evidence for verification.",
        ],
    )

    form = AdmissionTestForm(
        request.POST or None,
        request.FILES or None,
        instance=admission_test,
    )

    if not locked and request.method == "POST" and form.is_valid():
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

    if locked:
        for field in form.fields.values():
            field.disabled = True

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": title,
            "guidance": guidance,
            "step_guidance": step_guidance,
            "locked": locked,
            "lock_message": (
                "Your application has been submitted. Section I is now "
                "read-only."
            ),
        },
    )


@login_required
def step_admission_scheme(request):
    application = _get_or_create_application(request.user)
    admission_scheme = _get_or_build(AdmissionScheme, application)

    guidance = (
        "Indicate whether you are interested in the GAship or Day Scholar "
        "scheme."
    )

    step_guidance = _guidance(
        "Admission Scheme",
        [
            "Select the admission scheme that applies to you.",
            "Choose GAship or Day Scholar according to your preference.",
        ],
    )

    return _step(
        request,
        admission_scheme,
        AdmissionSchemeForm,
        "admission_scheme_status",
        "step_employment",
        "Admission Scheme",
        guidance,
        step_guidance,
    )


@login_required
def step_employment(request):
    application = _get_or_create_application(request.user)
    current_employment = _get_or_build(
        CurrentEmployment,
        application,
    )

    guidance = (
        "Skip this step if it does not apply to you."
    )

    step_guidance = _guidance(
        "Current Employment",
        [
            "Skip this section if it does not apply to you.",
            "Provide truthful and accurate employment information.",
            "False or misused information may result in cancellation of your application.",
        ],
    )

    return _step(
        request,
        current_employment,
        CurrentEmploymentForm,
        "employment_status",
        "application_form",
        "Current Employment",
        guidance,
        step_guidance,
    )


@login_required
def application_form(request):
    application = _get_or_create_application(request.user)
    locked = application.section_i_locked

    application_form_obj = _get_or_build(
        ApplicationForm,
        application,
    )

    form = ApplicationFormForm(
        request.POST or None,
        instance=application_form_obj,
    )

    if not locked and request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.status = "completed"
        updated.save()

        application.updated_at = timezone.now()
        application.save(update_fields=["updated_at"])

        return redirect("declaration")

    if locked:
        for field in form.fields.values():
            field.disabled = True

    return render(
        request,
        "applications/application_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "checklist": application.checklist_section_i,
            "progress_percent": int(
                round(
                    sum(
                        getattr(application, key) == "completed"
                        for key in application.SECTION_I_KEYS
                    )
                    / len(application.SECTION_I_KEYS)
                    * 100
                )
            ),
            "is_ready_for_submission": application.is_ready_for_submission,
            "locked": locked,
            "step_guidance": _guidance(
                "Form Submissions",
                [
                    "Review your complete application before submitting.",
                    "After submission, your application cannot be updated or changed.",
                    "Print the submitted form.",
                    "Courier the form with all required documents before the closing date.",
                ],
            ),
        },
    )


@login_required
def step_processing_fee(request):
    application = _get_or_create_application(request.user)
    processing_fee = _get_or_build(
        ProcessingFee,
        application,
    )

    form = ProcessingFeeForm(
        request.POST or None,
        request.FILES or None,
        instance=processing_fee,
    )

    guidance = (
        "Enter your payment details accurately."
    )

    step_guidance = _guidance(
        "Processing Fee",
        [
            "Select one of the available payment methods.",
            "Enter your payment details accurately.",
            "Attach your payment proof.",
            "Keep the original receipt for your records.",
        ],
    )

    if request.method == "POST" and form.is_valid():
        uploaded_proof = request.FILES.get("proof_of_payment")
        updated = form.save(commit=False)

        if uploaded_proof:
            encoded, content_type = _encode_file(uploaded_proof)
            updated.proof_of_payment = encoded
            updated.proof_of_payment_type = content_type

        updated.status = "completed"
        updated.save()

        application.updated_at = timezone.now()
        application.save(update_fields=["updated_at"])

        return redirect("application_status")

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": "Processing Fee",
            "guidance": guidance,
            "step_guidance": step_guidance,
        },
    )


@login_required
def step_referee_information(request):
    application = _get_or_create_application(request.user)
    referee_information = _get_or_build(
        RefereeInformation,
        application,
    )

    form = RefereeInformationForm(
        request.POST or None,
        request.FILES or None,
        instance=referee_information,
    )

    guidance = (
        "Complete all required fields"
    )

    step_guidance = _guidance(
        "Submission Guidelines",
        [
            "Complete all required fields.",
            "Upload two recommendation letters in an accepted format.",
            "Check your information and contact details carefully.",
            "Incomplete or incorrect information may result in rejection.",
        ],
    )

    if request.method == "POST" and form.is_valid():
        uploaded_letter = request.FILES.get("recommendation_letter")
        updated = form.save(commit=False)

        if uploaded_letter:
            encoded, content_type = _encode_file(uploaded_letter)
            updated.recommendation_letter = encoded
            updated.recommendation_letter_type = content_type

        updated.status = "completed"
        updated.save()

        application.updated_at = timezone.now()
        application.save(update_fields=["updated_at"])

        return redirect("application_status")

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": "Submission Guidelines",
            "guidance": guidance,
            "step_guidance": step_guidance,
        },
    )


@login_required
def step_test_center(request):
    application = _get_or_create_application(request.user)
    test_center = _get_or_build(
        TestCenter,
        application,
    )

    guidance = (
        "Review your assigned test center details carefully and confirm that "
        "the information is correct before continuing."
    )

    step_guidance = _guidance(
        "Test Center",
        [
            "Review your assigned test center carefully.",
            "Confirm that the information is correct before continuing.",
        ],
    )

    form = TestCenterForm(
        request.POST or None,
        instance=test_center,
    )

    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.status = "completed"
        updated.save()

        return redirect("application_status")

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": "Test Center",
            "guidance": guidance,
            "step_guidance": step_guidance,
        },
    )


@login_required
def declaration(request):
    application = _get_or_create_application(request.user)
    locked = application.section_i_locked

    guidance = (
        "Read the declaration carefully and make sure your application "
        "information is complete and accurate before accepting it."
    )

    step_guidance = _guidance(
        "Declaration",
        [
            "Read the declaration carefully.",
            "Make sure your application information is complete and accurate.",
            "Accept the declaration only after reviewing your information.",
        ],
    )

    form = DeclarationForm(
        request.POST or None,
        instance=application,
    )

    if not locked and request.method == "POST" and form.is_valid():
        form.save()
        return redirect("review_application")

    if locked:
        for field in form.fields.values():
            field.disabled = True

    return render(
        request,
        "applications/step_form.html",
        {
            "active_nav": "application",
            "application": application,
            "form": form,
            "title": "Declaration",
            "guidance": guidance,
            "step_guidance": step_guidance,
            "locked": locked,
            "lock_message": (
                "Your application has been submitted. Section I is now "
                "read-only."
            ),
        },
    )


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


@login_required
def submit_application(request):
    application = _get_or_create_application(request.user)

    if (
        request.method == "POST"
        and application.is_ready_for_submission
        and application.declaration_accepted
    ):
        already_submitted = application.status == "submitted"

        application.status = "submitted"
        application.submitted_at = timezone.now()
        application.save()

        if not already_submitted:
            notify(
                request.user,
                "Application Submitted",
                "Your application has been submitted successfully and is now locked for review.",
                "success",
            )

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

        ApplicationForm.objects.filter(
            application=application
        ).update(status="not_started")

        application.status = "draft"
        application.declaration_accepted = False
        application.submitted_at = None
        application.save()

    return redirect("my_application")


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