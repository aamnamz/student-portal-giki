from django.conf import settings
from django.db import models


class AdmissionCycle(models.Model):
    """
    Site-wide dates shown in 'Important Dates'. Keep exactly one row
    with is_active=True at a time; update it via the admin each cycle.
    """
    name = models.CharField(max_length=100, help_text="e.g. Fall 2026 Admissions")
    is_active = models.BooleanField(default=True)
    application_deadline = models.DateField(null=True, blank=True)
    document_deadline = models.DateField(null=True, blank=True)
    entry_test_date = models.DateField(null=True, blank=True)
    interview_date = models.DateField(null=True, blank=True)
    decision_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first() or cls.objects.first()


class Notice(models.Model):
    TYPE_CHOICES = [("info", "Info"), ("warn", "Warning"), ("danger", "Danger")]

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="notices",
        help_text="Leave blank to show this notice to every applicant.",
    )
    notice_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="info")
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Notification(models.Model):
    LEVEL_CHOICES = [
        ("info", "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("danger", "Danger"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="info")
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return self.title


def notify(user, title, message="", level="info", link=""):
    """Create an in-app notification for one user."""
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        level=level,
        link=link,
    )
