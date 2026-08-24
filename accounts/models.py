from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator


pakistani_phone = RegexValidator(
    r'^92\d{10}$',
    'Enter a valid phone number starting with 92 followed by 10 digits.',
)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=12, validators=[pakistani_phone], blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile: {self.user}"
