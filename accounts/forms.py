from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import RegexValidator

from .models import CustomUser, Profile, pakistani_phone


class StyledFormMixin:
    """Adds the CSS classes our templates expect (form-control /
    form-check-input) to every field's widget automatically, so we
    never have to remember to set them field-by-field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-check-input").strip()
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()


class SignUpForm(StyledFormMixin, UserCreationForm):
    PROGRAM_CHOICES = [
        ("MS", "MS"),
        ("PHD", "PhD"),
    ]
    program = forms.ChoiceField(
        choices=PROGRAM_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        error_messages={"required": "Please select the program you're applying for."},
    )
    name_validator = RegexValidator(r"^[A-Za-z]+(?:[-'][A-Za-z]+)*$", "Use letters only.")
    first_name = forms.CharField(max_length=150, required=True, validators=[name_validator])
    last_name = forms.CharField(max_length=150, required=True, validators=[name_validator])
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=12,
        required=False,
        validators=[pakistani_phone],
        widget=forms.TextInput(
            attrs={"placeholder": "923XXXXXXXXX"}
        ),
    )
    agree_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy",
    )

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "password1",
            "password2",
            "agree_terms",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get("phone_number", "")
            profile.save(update_fields=["phone"])
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=True, label="Remember me")
