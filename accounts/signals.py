from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import CustomUser, Profile
from dashboard.fcm import send_fcm_notification

from .models import CustomUser


@receiver(pre_save, sender=CustomUser)
def notify_on_password_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # new user being created, not a password change

    try:
        old_password = CustomUser.objects.get(pk=instance.pk).password
    except CustomUser.DoesNotExist:
        return

    if old_password and instance.password and old_password != instance.password:
        send_fcm_notification(
            instance,
            title="Password Changed",
            body="Your password was changed by an administrator. If this wasn't you, contact support immediately.",
            level="warning",
        )


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)