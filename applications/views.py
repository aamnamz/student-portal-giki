import base64

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Application, PersonalInfo, ContactAddress, AcademicInfo, GuardianInfo, AdditionalInfo
from .ai_models import validate_passport_image
from .forms import (
    AcademicInformationForm, AdditionalInformationForm, ContactAddressForm,
    DeclarationForm, GuardianInformationForm, PersonalInformationForm
)

STATUS_TIMELINE_STEPS = [
    "Registration",
    "Application Started",
    "Application Completed",
    "Submitted",
    "Under Review",
    "Decision",
]

# Maps Application.status -> how far along STATUS_TIMELINE_STEPS we are (0-indexed)
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


@login_required
def my_application(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    return render(request, "applications/overview.html", {
        "active_nav": "application",
        "checklist": application.checklist,
        "progress_percent": application.progress_percent,
        "is_ready_for_submission": application.is_ready_for_submission,
    })


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
        },
    )


@login_required
def declaration(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    form = DeclarationForm(request.POST or None, instance=application)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("review_application")
    return render(request, "applications/declaration.html", {"active_nav": "application", "application": application, "form": form})


@login_required
def review_application(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    return render(request, "applications/review.html", {
        "active_nav": "application", "application": application,
    })


@login_required
def submit_application(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    if request.method == "POST" and application.is_ready_for_submission and application.declaration_accepted:
        application.status = "submitted"
        application.submitted_at = timezone.now()
        application.save()
        return render(request, "applications/submit.html", {
            "active_nav": "application", "application": application, "submitted": True,
        })
    return redirect("review_application")


@login_required
def reset_application(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    if request.method == "POST":
        # Reset all section statuses
        PersonalInfo.objects.filter(application=application).update(status="not_started")
        ContactAddress.objects.filter(application=application).update(status="not_started")
        AcademicInfo.objects.filter(application=application).update(status="not_started")
        GuardianInfo.objects.filter(application=application).update(status="not_started")
        AdditionalInfo.objects.filter(application=application).update(status="not_started")
        
        # Reset application status
        application.status = "draft"
        application.declaration_accepted = False
        application.save()
    return redirect("my_application")


@login_required
def application_status(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    return render(request, "applications/status.html", {
        "active_nav": "status",
        "application": application,
        "status_timeline": _build_timeline(application),
    })
