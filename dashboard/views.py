from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

import json
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse

from .models import FCMDeviceToken

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from applications.models import Application

from .models import AdmissionCycle, Notice, Notification

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
            ("Application Deadline", cycle.application_deadline, True, True),
            ("Entry Test Date", cycle.entry_test_date, False,
             application.status in ("submitted", "under_review", "action_required") and not application.test_completed),
            ("Interview Date", cycle.interview_date, False,
             application.test_completed and not application.interview_attended),
            ("Admission Decision Date", cycle.decision_date, False,
             application.interview_attended),
        ]
        for label, value, urgent, visible in date_fields:
            if not visible:
                continue
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


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    Notification.objects.filter(pk=notification_id, user=request.user).update(is_read=True)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def clear_all_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def register_fcm_token(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return HttpResponseBadRequest("Invalid JSON")

    token = payload.get("token", "").strip()
    device_type = payload.get("device_type", "web")
    if not token:
        return HttpResponseBadRequest("Missing token")

    FCMDeviceToken.objects.update_or_create(
        token=token,
        defaults={"user": request.user, "device_type": device_type},
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def unregister_fcm_token(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return HttpResponseBadRequest("Invalid JSON")

    token = payload.get("token", "").strip()
    if not token:
        return HttpResponseBadRequest("Missing token")

    FCMDeviceToken.objects.filter(token=token, user=request.user).delete()
    return JsonResponse({"ok": True})


def firebase_messaging_sw_view(request):
    sw_path = Path(settings.BASE_DIR) / "firebase-messaging-sw.js"
    content = sw_path.read_text(encoding="utf-8")
    return HttpResponse(content, content_type="application/javascript")