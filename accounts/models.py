from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


pakistani_phone = RegexValidator(
    r'^92\d{10}$',
    'Enter a valid phone number starting with 92 followed by 10 digits.',
)

class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser for future role-based access control.
    Can add fields like role, department, etc. without altering the auth system.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Administrator'),
        ('staff', 'Staff'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text='User role for access control'
    )
    
    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class Profile(models.Model):
    """
    User profile containing additional user metadata.
    Keeps the auth system clean by separating profile data.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=12, validators=[pakistani_phone], blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)

    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"Profile: {self.user}"

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()

        if phone.startswith("03") and len(phone) == 11:
            return "92" + phone[1:]

        return phone
