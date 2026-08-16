from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from .models import Profile


class SignUpForm(UserCreationForm):
    name_validator = RegexValidator(r"^[A-Za-z]+(?:[-'][A-Za-z]+)*$", "Use letters only.")
    first_name = forms.CharField(max_length=150, required=True, validators=[name_validator])
    last_name = forms.CharField(max_length=150, required=True, validators=[name_validator])
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            Profile.objects.get_or_create(user=user)
        return user
