import base64

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from applications.models import Application
from applications.ai_models import validate_passport_image

from .forms import SignUpForm
from .models import Profile


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def my_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    application, _ = Application.objects.get_or_create(applicant=request.user)
    photo_error = None
    if request.method == "POST" and request.FILES.get("student_photo"):
        uploaded_photo = request.FILES["student_photo"]
        uploaded_photo.seek(0)
        is_valid, error_message = validate_passport_image(uploaded_photo)
        if is_valid:
            uploaded_photo.seek(0)
            application.student_photo = base64.b64encode(uploaded_photo.read()).decode("ascii")
            application.student_photo_type = uploaded_photo.content_type or "image/jpeg"
            application.save(update_fields=["student_photo", "student_photo_type", "updated_at"])
            return redirect("my_profile")
        photo_error = error_message
    return render(request, "accounts/profile.html", {
        "active_nav": "profile",
        "profile": profile,
        "application": application,
        "photo_error": photo_error,
    })


@login_required
def settings_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "accounts/settings.html", {
        "active_nav": "settings",
        "profile": profile,
    })
