from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    checklist = [
        {"name": "Personal Information", "status_key": "completed", "status_label": "Completed"},
        {"name": "Contact & Address", "status_key": "completed", "status_label": "Completed"},
        {"name": "Academic Information", "status_key": "inprogress", "status_label": "In Progress"},
        {"name": "Guardian Information", "status_key": "notstarted", "status_label": "Not Started"},
        {"name": "Documents", "status_key": "needscorrection", "status_label": "Needs Correction"},
    ]

    status_timeline = [
        {"label": "Registration", "done": True, "current": False},
        {"label": "Application Started", "done": True, "current": False},
        {"label": "Application Completed", "done": False, "current": True},
        {"label": "Submitted", "done": False, "current": False},
        {"label": "Under Review", "done": False, "current": False},
        {"label": "Decision", "done": False, "current": False},
    ]

    important_dates = [
        {"label": "Application Deadline", "value": "August 30, 2026", "urgent": True},
        {"label": "Document Submission Deadline", "value": "September 3, 2026", "urgent": False},
        {"label": "Entry Test Date", "value": "September 15, 2026", "urgent": False},
        {"label": "Interview Date", "value": "To be announced", "urgent": False},
        {"label": "Admission Decision Date", "value": "October 10, 2026", "urgent": False},
    ]

    notices = [
        {"type": "warn", "title": "Application deadline is in 18 days", "meta": "Reminder · Aug 12, 2026"},
        {"type": "danger", "title": "Domicile certificate needs correction", "meta": "Documents · Aug 10, 2026"},
        {"type": "info", "title": "Admissions office: campus visit day announced", "meta": "Announcement · Aug 8, 2026"},
    ]

    context = {
        "active_nav": "dashboard",
        "applicant_name": request.user.get_full_name() or request.user.username,
        "applicant_initials": "".join([n[0] for n in (request.user.get_full_name() or "A A").split()[:2]]).upper(),
        "notification_count": 3,

        "application_deadline": "Aug 30, 2026",
        "progress_percent": 40,
        "sections_completed": 2,
        "sections_total": 5,
        "primary_action": "Continue Application",

        "status_key": "inprogress",
        "status_label": "In Progress",
        "status_timeline": status_timeline,

        "checklist": checklist,
        "important_dates": important_dates,

        "docs_uploaded": 3,
        "docs_missing": 2,
        "docs_pending": 1,
        "docs_correction": 1,

        "notices": notices,
    }
    return render(request, "dashboard.html", context)


# ---------------------------------------------------------------------
# Placeholder views below — one per sidebar/navbar link.
# Each just renders a template with active_nav set so the sidebar
# highlights correctly. Replace bodies as you build each page out.
# ---------------------------------------------------------------------

@login_required
def my_application(request):
    return render(request, "application/overview.html", {"active_nav": "application"})


@login_required
def step_personal_information(request):
    return render(request, "application/step_personal_information.html", {"active_nav": "application"})


@login_required
def step_contact_address(request):
    return render(request, "application/step_contact_address.html", {"active_nav": "application"})


@login_required
def step_academic_information(request):
    return render(request, "application/step_academic_information.html", {"active_nav": "application"})


@login_required
def step_guardian_information(request):
    return render(request, "application/step_guardian_information.html", {"active_nav": "application"})


@login_required
def review_application(request):
    return render(request, "application/review.html", {"active_nav": "application"})


@login_required
def submit_application(request):
    return render(request, "application/submit.html", {"active_nav": "application"})


@login_required
def documents(request):
    return render(request, "documents.html", {"active_nav": "documents"})


@login_required
def my_profile(request):
    return render(request, "profile.html", {"active_nav": "profile"})


@login_required
def application_status(request):
    return render(request, "status.html", {"active_nav": "status"})


@login_required
def settings_view(request):
    return render(request, "settings.html", {"active_nav": "settings"})


@login_required
def help_contact(request):
    return render(request, "help.html", {"active_nav": "help"})