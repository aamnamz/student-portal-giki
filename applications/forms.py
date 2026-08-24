from django import forms

from .models import Application


class PortalForm(forms.ModelForm):
    """Shared Bootstrap 5 validation defaults for the application steps."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-select" if isinstance(field.widget, forms.Select) else "form-control")
            field.required = True

        for name, field in self.fields.items():
            if "phone" in name or name == "emergency_contact_number":
                field.widget.attrs.update({
                    "inputmode": "numeric",
                    "pattern": "92[0-9]{10}",
                    "maxlength": "12",
                    "placeholder": "923XXXXXXXXX",
                })
            elif "cnic" in name:
                field.widget.attrs.update({"inputmode": "numeric", "pattern": "[0-9]{5}-[0-9]{7}-[0-9]", "maxlength": "15", "placeholder": "12345-1234567-1"})
            elif name == "postal_code":
                field.widget.attrs.update({"inputmode": "numeric", "pattern": "[0-9]{4,6}", "maxlength": "6"})


class PersonalInformationForm(PortalForm):
    student_photo = forms.ImageField(required=False)

    class Meta:
        model = Application
        fields = ["student_photo", "first_name", "last_name", "father_name", "mother_name", "date_of_birth", "cnic_or_bform", "blood_group", "gender", "marital_status", "nationality", "religion"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), 
                   "blood_group": forms.Select(choices=[("", "Select blood group"), ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"), ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-")]), 
                   "gender": forms.Select(choices=[("", "Select gender"), *Application.GENDER_CHOICES]), 
                   "marital_status": forms.Select(choices=[("", "Select marital status"), ("single", "Single"), ("married", "Married")]), 
                   "nationality": forms.Select(choices=[("", "Select nationality"), ("Pakistani", "Pakistani"), ("Other", "Other")]), 
                   "religion": forms.Select(choices=[("", "Select religion"), ("Islam", "Islam"), ("Christianity", "Christianity"), ("Hinduism", "Hinduism"), ("Sikhism", "Sikhism"), ("Other", "Other")])
                   }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_photo"].required = not bool(self.instance.student_photo)


class ContactAddressForm(PortalForm):
    class Meta:
        model = Application
        fields = ["phone", "alternate_phone", "present_address", "permanent_address", "city", "district", "province", "postal_code", "domicile_province", "domicile_district"]
        widgets = {"present_address": forms.Textarea(attrs={"rows": 4, "maxlength": 200}), "permanent_address": forms.Textarea(attrs={"rows": 4, "maxlength": 200}), "province": forms.Select(choices=[("", "Select province"), *Application._meta.get_field("province").choices]), "domicile_province": forms.Select(choices=[("", "Select domicile province"), *Application._meta.get_field("domicile_province").choices])}


class AcademicInformationForm(PortalForm):
    class Meta:
        model = Application
        fields = ["matric_board", "matric_year", "matric_total_marks", "matric_marks", "matric_grade", "intermediate_result", "intermediate_board", "intermediate_group", "intermediate_year", "intermediate_total_marks", "intermediate_marks", "intermediate_grade", "degree_program"]
        widgets = {"matric_board": forms.Select(choices=[("", "Select matric group"), ("Biology", "Biology"), ("Computer", "Computer")]), "intermediate_result": forms.Select(choices=[("", "Select intermediate result"), ("passed", "Result Available"), ("awaited", "Result Awaited")]), "intermediate_group": forms.Select(choices=[("", "Select group"), ("Pre-Engineering", "Pre-Engineering"), ("Pre-Medical", "Pre-Medical"), ("Computer Science", "Computer Science"), ("Humanities", "Humanities"), ("Commerce", "Commerce")]), "degree_program": forms.Select(choices=[("", "Select degree program"), ("BS Aerospace Engineering", "BS Aerospace Engineering"), ("BS Computer Science", "BS Computer Science"), ("BS Cybersecurity", "BS Cybersecurity"), ("BS Data Science", "BS Data Science"), ("BS Chemical Engineering", "BS Chemical Engineering"), ("BS Software Engineering", "BS Software Engineering"), ("BS Civil Engineering", "BS Civil Engineering"), ("BS Mechanical Engineering", "BS Mechanical Engineering")])}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        numeric_fields = ("matric_year", "matric_total_marks", "matric_marks", "intermediate_year", "intermediate_total_marks", "intermediate_marks")
        for name in numeric_fields:
            self.fields[name].widget = forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "pattern": "[0-9]+", "maxlength": "4"})

        result = self.data.get(self.add_prefix("intermediate_result")) if self.is_bound else self.instance.intermediate_result
        if result == "awaited":
            for name in ("intermediate_board", "intermediate_group", "intermediate_year", "intermediate_total_marks", "intermediate_marks", "intermediate_grade"):
                self.fields[name].required = False


class GuardianInformationForm(PortalForm):
    class Meta:
        model = Application
        fields = ["guardian_name", "guardian_relationship", "guardian_occupation", "guardian_phone", "guardian_cnic", "guardian_income", "emergency_contact_name", "emergency_contact_relationship", "emergency_contact_number"]
        widgets = {"guardian_relationship": forms.Select(choices=[("", "Select relationship"), ("Father", "Father"), ("Mother", "Mother"), ("Brother", "Brother"), ("Sister", "Sister"), ("Uncle", "Uncle"), ("Legal Guardian", "Legal Guardian"), ("Other", "Other")])}


class AdditionalInformationForm(PortalForm):
    class Meta:
        model = Application
        fields = ["hostel_required", "scholarship_required", "disability_status"]
        widgets = {
            "hostel_required": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            "scholarship_required": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
            "disability_status": forms.RadioSelect(choices=[(True, "Yes"), (False, "No")]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-check-input"


class DeclarationForm(PortalForm):
    declaration_accepted = forms.BooleanField(label="I certify that the information provided is true.")
    class Meta:
        model = Application
        fields = ["declaration_accepted"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["declaration_accepted"].widget.attrs["class"] = "form-check-input"
