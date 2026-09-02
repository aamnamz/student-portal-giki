from django import forms

from .models import (
    PersonalInfo,
    ContactAddress,
    AcademicInfo,
    ProgramPreference,
    AdmissionTest,
    AdmissionScheme,
    CurrentEmployment,
    ApplicationForm,
    ProcessingFee,
    RefereeInformation,
    TestCenter,
    Application,
)


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
            elif isinstance(widget, (forms.RadioSelect,)):
                # Radios are styled per-option in the template, not here.
                continue
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()


# ---------------------------------------------------------------------------
# Section 1: Personal Information
# ---------------------------------------------------------------------------
class PersonalInformationForm(StyledFormMixin, forms.ModelForm):
    # student_photo on the model is a TextField holding a base64 string —
    # the view compresses/encodes the upload and writes it there itself.
    # This field exists only to render a real file-upload widget; it is
    # deliberately left OUT of Meta.fields below so Django's save/
    # construct_instance machinery never touches the model's student_photo
    # TextField directly — that's the view's job (see step_personal_
    # information / _step_personal). Leaving it in Meta.fields would wipe
    # out an existing photo any time the form is resubmitted without a new
    # upload.
    student_photo = forms.ImageField(
        required=False,
        help_text="Upload a passport-size photo (JPG or PNG).",
    )

    class Meta:
        model = PersonalInfo
        fields = [
            "full_name",
            "father_name",
            "guardian_name",
            "guardian_contact_no",
            "cell_no",
            "religion",
            "date_of_birth",
            "gender",
            "nationality",
            "cnic",
            "passport_no",
            "domicile_province",
            "domicile_district",
            "disability_status",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "gender": forms.RadioSelect,
            "disability_status": forms.RadioSelect,
            "nationality": forms.Select(
                attrs={"data-nationality-select": "true"}
            ),
            "cnic": forms.TextInput(
                attrs={
                    "placeholder": "12345-1234567-1",
                    "data-nationality-toggle": "Pakistani",
                    "inputmode": "numeric",
                }
            ),
            "passport_no": forms.TextInput(
                attrs={
                    "placeholder": "AB1234567",
                    "data-nationality-toggle": "Other",
                }
            ),
            "guardian_contact_no": forms.TextInput(
                attrs={
                    "placeholder": "923XXXXXXXXX",
                    "inputmode": "numeric",
                    "maxlength": "12",
                }
            ),
            "cell_no": forms.TextInput(
                attrs={
                    "placeholder": "923XXXXXXXXX",
                    "inputmode": "numeric",
                    "maxlength": "12",
                }
            ),
            "full_name": forms.TextInput(attrs={"pattern": "[A-Za-z '\\-]+"}),
            "father_name": forms.TextInput(attrs={"pattern": "[A-Za-z '\\-]+"}),
            "guardian_name": forms.TextInput(attrs={"pattern": "[A-Za-z '\\-]+"}),
            "domicile_district": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # guardian_name is the only field on this form that isn't required.
        self.fields["guardian_name"].required = False
        # cnic / passport_no are conditionally required — enforced in
        # clean(), not here, so the empty one never blocks submission.
        self.fields["cnic"].required = False
        self.fields["passport_no"].required = False

    def clean(self):
        cleaned_data = super().clean()
        nationality = cleaned_data.get("nationality")
        cnic = cleaned_data.get("cnic")
        passport_no = cleaned_data.get("passport_no")

        if nationality == "Pakistani":
            if not cnic:
                self.add_error(
                    "cnic", "CNIC is required for Pakistani nationals."
                )
            if passport_no:
                self.add_error(
                    "passport_no",
                    "Passport number should only be provided for "
                    "non-Pakistani nationals.",
                )
        else:
            if not passport_no:
                self.add_error(
                    "passport_no",
                    "Passport number is required for non-Pakistani "
                    "nationals.",
                )
            if cnic:
                self.add_error(
                    "cnic",
                    "CNIC should only be provided for Pakistani nationals.",
                )

        return cleaned_data


# ---------------------------------------------------------------------------
# Section 2: Contact & Address
# ---------------------------------------------------------------------------
class ContactAddressForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactAddress
        fields = [
            "mailing_same_as_permanent",
            "permanent_house_street_no",
            "permanent_mohalla_tehsil",
            "permanent_district",
            "permanent_city",
            "permanent_phone",
            "permanent_courier_available",
            "mailing_house_street_no",
            "mailing_mohalla_tehsil",
            "mailing_district",
            "mailing_city",
            "mailing_phone",
            "mailing_courier_available",
        ]
        widgets = {
            "mailing_same_as_permanent": forms.CheckboxInput(
                attrs={"data-same-as-toggle": "mailing-address-fields"}
            ),
            "permanent_phone": forms.TextInput(
                attrs={
                    "placeholder": "923XXXXXXXXX",
                    "inputmode": "numeric",
                    "maxlength": "12",
                }
            ),
            "mailing_phone": forms.TextInput(
                attrs={
                    "placeholder": "923XXXXXXXXX",
                    "inputmode": "numeric",
                    "maxlength": "12",
                }
            ),
            "permanent_courier_available": forms.CheckboxInput(),
            "mailing_courier_available": forms.CheckboxInput(),
            "permanent_mohalla_tehsil": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
            "permanent_district": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
            "permanent_city": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
            "mailing_mohalla_tehsil": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
            "mailing_district": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
            "mailing_city": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Courier-available is the only genuinely optional field on either
        # address block; everything else in "mailing" is only optional at
        # the widget level because it may get filled in by JS/clean().
        for field in [
            "permanent_courier_available",
            "mailing_courier_available",
            "mailing_house_street_no",
            "mailing_mohalla_tehsil",
            "mailing_district",
            "mailing_city",
            "mailing_phone",
        ]:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("mailing_same_as_permanent"):
            cleaned_data["mailing_house_street_no"] = cleaned_data.get(
                "permanent_house_street_no"
            )
            cleaned_data["mailing_mohalla_tehsil"] = cleaned_data.get(
                "permanent_mohalla_tehsil"
            )
            cleaned_data["mailing_district"] = cleaned_data.get(
                "permanent_district"
            )
            cleaned_data["mailing_city"] = cleaned_data.get("permanent_city")
            cleaned_data["mailing_phone"] = cleaned_data.get(
                "permanent_phone"
            )
            cleaned_data["mailing_courier_available"] = cleaned_data.get(
                "permanent_courier_available"
            )
            return cleaned_data

        required_when_different = [
            "mailing_house_street_no",
            "mailing_mohalla_tehsil",
            "mailing_district",
            "mailing_city",
            "mailing_phone",
        ]
        for field in required_when_different:
            if not cleaned_data.get(field):
                self.add_error(
                    field,
                    "This field is required unless 'same as permanent "
                    "address' is checked.",
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("mailing_same_as_permanent"):
            instance.mailing_house_street_no = self.cleaned_data[
                "mailing_house_street_no"
            ]
            instance.mailing_mohalla_tehsil = self.cleaned_data[
                "mailing_mohalla_tehsil"
            ]
            instance.mailing_district = self.cleaned_data["mailing_district"]
            instance.mailing_city = self.cleaned_data["mailing_city"]
            instance.mailing_phone = self.cleaned_data["mailing_phone"]
            instance.mailing_courier_available = self.cleaned_data[
                "mailing_courier_available"
            ]
        if commit:
            instance.save()
        return instance


# ---------------------------------------------------------------------------
# Section 3: Previous / Academic Education
# ---------------------------------------------------------------------------

# Reference mapping for the dependent Board/University dropdown. Dump this
# to the template with `{{ boards_by_degree|json_script:"boards-by-degree" }}`
# and have your JS repopulate the board_university <select>/<datalist>
# whenever degree_certificate changes.
BOARDS_BY_DEGREE = {
    "matric": [
        "BISE Peshawar", "BISE Lahore", "BISE Karachi",
        "Federal Board (FBISE)", "Other",
    ],
    "intermediate": [
        "BISE Peshawar", "BISE Lahore", "BISE Karachi",
        "Federal Board (FBISE)", "Cambridge (A-Level)", "Other",
    ],
    "bachelor": [
        "University of Peshawar", "Punjab University", "Karachi University",
        "NUST", "COMSATS", "Other",
    ],
    "master": [
        "University of Peshawar", "Punjab University", "Karachi University",
        "NUST", "COMSATS", "Other",
    ],
    "other": ["Other"],
}


class AcademicInformationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicInfo
        fields = [
            "degree_certificate",
            "board_university",
            "degree_title",
            "institute_name",
            "obtained_marks",
            "total_marks",
            "passing_year",
            "study_group",
            "country_studied",
            "result_declared",
        ]
        widgets = {
            "degree_certificate": forms.Select(
                attrs={"data-degree-select": "true"}
            ),
            "board_university": forms.TextInput(
                attrs={
                    "list": "board-university-options",
                    "data-degree-target": "true",
                }
            ),
            "result_declared": forms.RadioSelect,
            "passing_year": forms.NumberInput(
                attrs={"min": 1950, "max": 2035}
            ),
            "country_studied": forms.TextInput(
                attrs={"pattern": "[A-Za-z '\\-]+"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["degree_certificate"].choices = [
            c for c in self.fields["degree_certificate"].choices if c[0]
        ]

    def clean(self):
        cleaned_data = super().clean()
        obtained_marks = cleaned_data.get("obtained_marks")
        total_marks = cleaned_data.get("total_marks")

        if (
            obtained_marks is not None
            and total_marks is not None
            and obtained_marks > total_marks
        ):
            self.add_error(
                "obtained_marks",
                "Obtained marks/CGPA cannot exceed total marks/scale.",
            )

        return cleaned_data


# ---------------------------------------------------------------------------
# Section 4: Program Preferences
# ---------------------------------------------------------------------------
class ProgramPreferenceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ProgramPreference
        fields = ["degree_level", "discipline"]


# ---------------------------------------------------------------------------
# Section 5: Admission Test
# ---------------------------------------------------------------------------
class AdmissionTestForm(StyledFormMixin, forms.ModelForm):
    # Same base64-in-TextField pattern as PersonalInformationForm's
    # student_photo — kept out of Meta.fields, the view writes to
    # evidence_document/evidence_document_type itself.
    evidence_document = forms.FileField(
        required=False,
        help_text="Upload proof of your qualified entrance test result "
        "(PDF, JPG, or PNG).",
    )

    class Meta:
        model = AdmissionTest
        fields = [
            "entry_test_option",
            "test_center",
            "test_center_name",
            "test_type",
            "obtained_marks",
            "total_marks",
            "date_of_test",
        ]
        widgets = {
            "entry_test_option": forms.RadioSelect(
                attrs={"data-entry-test-toggle": "true"}
            ),
            "date_of_test": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "test_center_name": forms.TextInput(
                attrs={"data-already-qualified-field": "true"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["entry_test_option"].choices = [
            c for c in self.fields["entry_test_option"].choices if c[0]
        ]
        # These five are only required when entry_test_option is
        # "already_qualified" — enforced in clean(), not here.
        for field in [
            "test_center_name",
            "test_type",
            "obtained_marks",
            "total_marks",
            "date_of_test",
        ]:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        entry_test_option = cleaned_data.get("entry_test_option")

        if entry_test_option != "already_qualified":
            return cleaned_data

        required_fields = [
            "test_center_name",
            "test_type",
            "obtained_marks",
            "total_marks",
            "date_of_test",
        ]
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(
                    field,
                    "This field is required when you have already "
                    "qualified the entrance test.",
                )

        obtained_marks = cleaned_data.get("obtained_marks")
        total_marks = cleaned_data.get("total_marks")
        if (
            obtained_marks is not None
            and total_marks is not None
            and obtained_marks > total_marks
        ):
            self.add_error(
                "obtained_marks",
                "Obtained marks cannot exceed total marks.",
            )

        return cleaned_data


# ---------------------------------------------------------------------------
# Section 6: Admission Scheme
# ---------------------------------------------------------------------------
class AdmissionSchemeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AdmissionScheme
        fields = [
            "admission_scheme",
            "ga_ship_interest",
            "day_scholar_interest",
        ]
        widgets = {
            "ga_ship_interest": forms.RadioSelect(
                choices=[(True, "Yes"), (False, "No")]
            ),
            "day_scholar_interest": forms.RadioSelect(
                choices=[(True, "Yes"), (False, "No")]
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ga_ship_interest"].required = False
        self.fields["day_scholar_interest"].required = False


# ---------------------------------------------------------------------------
# Section 7: Current Employment
# ---------------------------------------------------------------------------
class CurrentEmploymentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = CurrentEmployment
        fields = [
            "no_employment_history",
            "employer",
            "job_title",
            "date_of_joining",
            "still_working_here",
        ]
        widgets = {
            "no_employment_history": forms.CheckboxInput(
                attrs={"data-same-as-toggle": "employment-fields"}
            ),
            "date_of_joining": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "job_title": forms.TextInput(attrs={"pattern": "[A-Za-z '\\-]+"}),
            "still_working_here": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only required unless "No Employment History" is checked —
        # enforced in clean(), not here.
        for field in [
            "employer",
            "job_title",
            "date_of_joining",
            "still_working_here",
        ]:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("no_employment_history"):
            return cleaned_data

        required_fields = ["employer", "job_title", "date_of_joining"]
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(
                    field,
                    "This field is required unless 'No Employment "
                    "History' is checked.",
                )

        return cleaned_data


# ---------------------------------------------------------------------------
# Section 8: Application Form
# ---------------------------------------------------------------------------
class ApplicationFormForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ApplicationForm
        fields = []

# ---------------------------------------------------------------------------
# SECTION II
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 9. Processing Fee
# ---------------------------------------------------------------------------
class ProcessingFeeForm(StyledFormMixin, forms.ModelForm):
    # Same base64-in-TextField pattern as PersonalInformationForm's
    # student_photo — kept out of Meta.fields, the view writes to
    # proof_of_payment/proof_of_payment_type itself.
    proof_of_payment = forms.FileField(
        required=False,
        help_text="Attach your payment receipt/slip (PDF, JPG, or PNG).",
    )

    class Meta:
        model = ProcessingFee
        fields = [
            "bank_provider_name",
            "payment_mode",
            "payment_date",
            "amount",
            "reference_number",
            "fee_deposited",
        ]
        widgets = {
            "payment_date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "amount": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
            "fee_deposited": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fee_deposited"].required = False


# ---------------------------------------------------------------------------
# 10. References & LOR
# ---------------------------------------------------------------------------
class RefereeInformationForm(StyledFormMixin, forms.ModelForm):
    # Same base64-in-TextField pattern as PersonalInformationForm's
    # student_photo — kept out of Meta.fields, the view writes to
    # recommendation_letter/recommendation_letter_type itself.
    recommendation_letter = forms.FileField(
        required=False,
        help_text="Upload the signed Letter of Recommendation "
        "(PDF, JPG, or PNG).",
    )

    class Meta:
        model = RefereeInformation
        fields = [
            "referee_name",
            "contact_number",
            "email",
            "university_name",
            "designation",
        ]
        widgets = {
            "contact_number": forms.TextInput(
                attrs={
                    "placeholder": "923XXXXXXXXX",
                    "inputmode": "numeric",
                    "maxlength": "12",
                }
            ),
            "referee_name": forms.TextInput(attrs={"pattern": "[A-Za-z '\\-]+"}),
            "designation": forms.TextInput(attrs={"pattern": "[A-Za-z '\\-]+"}),
        }


# ---------------------------------------------------------------------------
# SECTION III
# 11. Test Center
#
# The model only has a status field for now (see the comment above
# TestCenter in models.py) — this form mirrors that until the required
# fields are confirmed.
# ---------------------------------------------------------------------------
class TestCenterForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TestCenter
        fields = ["preferred_test_center"]

# ---------------------------------------------------------------------------
# Declaration
# ---------------------------------------------------------------------------
class DeclarationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Application
        fields = ["declaration_accepted"]
        labels = {
            "declaration_accepted": (
                "I declare that the information provided in this "
                "application is true and complete to the best of my "
                "knowledge."
            ),
        }

    def clean_declaration_accepted(self):
        accepted = self.cleaned_data.get("declaration_accepted")
        if not accepted:
            raise forms.ValidationError(
                "You must accept the declaration to continue."
            )
        return accepted