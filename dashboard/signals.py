from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .fcm import send_fcm_notification
from .models import AdmissionCycle


def _everyone(Application):
    return Application.objects.values_list("applicant", flat=True).distinct()


def _submitted_not_tested(Application):
    return Application.objects.filter(
        status__in=["submitted", "under_review", "action_required"],
        test_completed=False,
    ).values_list("applicant", flat=True).distinct()


def _tested_not_interviewed(Application):
    return Application.objects.filter(
        test_completed=True,
        interview_attended=False,
    ).values_list("applicant", flat=True).distinct()


def _interviewed(Application):
    return Application.objects.filter(
        interview_attended=True,
    ).values_list("applicant", flat=True).distinct()


_DATE_FIELD_CONFIG = {
    "application_deadline": {"title": "Application Deadline Updated", "audience": _everyone},
    "document_deadline": {"title": "Document Deadline Updated", "audience": _everyone},
    "entry_test_date": {"title": "Entry Test Date Announced", "audience": _submitted_not_tested},
    "interview_date": {"title": "Interview Date Announced", "audience": _tested_not_interviewed},
    "decision_date": {"title": "Decision Date Announced", "audience": _interviewed},
}


@receiver(pre_save, sender=AdmissionCycle)
def stash_old_dates(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_dates = {}
        return
    try:
        old = AdmissionCycle.objects.get(pk=instance.pk)
    except AdmissionCycle.DoesNotExist:
        instance._old_dates = {}
        return
    instance._old_dates = {field: getattr(old, field) for field in _DATE_FIELD_CONFIG}


@receiver(post_save, sender=AdmissionCycle)
def notify_on_date_change(sender, instance, created, **kwargs):
    if created:
        return

    from applications.models import Application
    from django.contrib.auth import get_user_model
    User = get_user_model()

    old_dates = getattr(instance, "_old_dates", {})
    changed_fields = {
        field: getattr(instance, field)
        for field in _DATE_FIELD_CONFIG
        if getattr(instance, field) and getattr(instance, field) != old_dates.get(field)
    }
    if not changed_fields:
        return

    for field, new_value in changed_fields.items():
        config = _DATE_FIELD_CONFIG[field]
        title = config["title"]
        body = f"{title.replace(' Announced', '').replace(' Updated', '')}: {new_value.strftime('%B %d, %Y')}"
        user_ids = config["audience"](Application)
        for user in User.objects.filter(pk__in=user_ids):
            send_fcm_notification(user, title=title, body=body, link="/")