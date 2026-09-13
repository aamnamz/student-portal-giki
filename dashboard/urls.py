from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("help/", views.help_contact, name="help_contact"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/clear/", views.clear_all_notifications, name="clear_all_notifications"),
    path("api/fcm/register/", views.register_fcm_token, name="register_fcm_token"),
    path("api/fcm/unregister/", views.unregister_fcm_token, name="unregister_fcm_token"),
]
