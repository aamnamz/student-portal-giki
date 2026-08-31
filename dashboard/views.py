from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from applications.models import Application

from .models import AdmissionCycle, Notice

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


@login_required
def dashboard(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)
    cycle = AdmissionCycle.get_active()
    important_dates = []
    if cycle:
        date_fields = [
            ("Application Deadline", cycle.application_deadline, True),
            ("Entry Test Date", cycle.entry_test_date, False),
            ("Interview Date", cycle.interview_date, False),
            ("Admission Decision Date", cycle.decision_date, False),
        ]
        for label, value, urgent in date_fields:
            important_dates.append({
                "label": label,
                "value": value.strftime("%B %d, %Y") if value else "To be announced",
                "urgent": urgent and bool(value),
            })

    notices_qs = (Notice.objects.filter(applicant__isnull=True) | Notice.objects.filter(applicant=request.user))
    notices_qs = notices_qs.order_by("-created_at")[:5]

    if application.status == "draft" and application.sections_completed_count == 0:
        primary_action = "Start Application"
    elif application.is_ready_for_submission:
        primary_action = "Review Application"
    elif application.status in ("submitted", "under_review", "accepted", "rejected", "action_required"):
        primary_action = "View Application"
    else:
        primary_action = "Continue Application"

    context = {
        "active_nav": "dashboard",
        "applicant_name": request.user.get_full_name() or request.user.username,
        "applicant_email": request.user.email,
        "today": timezone.localdate(),
        "applicant_initials": "".join(
            [n[0] for n in (request.user.get_full_name() or "A A").split()[:2]]
        ).upper(),
        "notification_count": notices_qs.count(),

        "application_deadline": important_dates[0]["value"] if important_dates else "To be announced",
        "progress_percent": application.progress_percent,
        "sections_completed": application.sections_completed_count,
        "sections_total": application.sections_total,
        "primary_action": primary_action,

        "status_key": application.status.replace("_", ""),
        "status_label": application.get_status_display(),
        "status_timeline": _build_timeline(application),

        "checklist": application.checklist,
        "important_dates": important_dates,

        "notices": [
            {"type": n.notice_type, "title": n.title, "meta": n.created_at.strftime("%b %d, %Y")}
            for n in notices_qs
        ],
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def help_contact(request):
    return render(request, "dashboard/help.html", {"active_nav": "help"})
