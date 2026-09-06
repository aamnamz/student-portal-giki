from applications.models import Application

from .models import Notification


def portal_context(request):
    """Shared topbar data for authenticated portal users."""
    if not request.user.is_authenticated:
        return {}

    application, _ = Application.objects.get_or_create(applicant=request.user)
    full_name = request.user.get_full_name()
    source_name = full_name or request.user.username
    applicant_initials = "".join(part[0] for part in source_name.split()[:2]).upper()

    notifications = Notification.objects.filter(user=request.user)
    return {
        "application": application,
        "applicant_initials": applicant_initials,
        "notification_count": notifications.filter(is_read=False).count(),
        "recent_notifications": notifications[:8],
    }
