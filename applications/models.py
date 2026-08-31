from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models


# ---------------------------------------------------------------------------
# Shared validators
#
# Rule of thumb used throughout this file:
#   - Any field that holds a PERSON'S NAME or a place name (city, district,
#     tehsil, country, job title, designation ...) uses `letters_and_spaces`
#     (or `letters_only`) so digits/symbols are rejected outright.
#   - Any field that holds an ORGANISATION name (bank, employer, institute,
#     university, program) uses `institute_name_validator`, which allows
#     digits/&/.,'- because real org names legitimately contain them
#     (e.g. "3M Pakistan", "K-Electric", "FBISE").
#   - Any PHONE NUMBER field uses `pakistani_phone`, which is digits-only
#     by construction (^92\d{10}$) -> letters can never be entered/saved.
# ---------------------------------------------------------------------------
letters_only = RegexValidator(
    r"^[A-Za-z]+(?:[-'][A-Za-z]+)*$",
    "Use letters only.",
)

letters_and_spaces = RegexValidator(
    r"^[A-Za-z]+(?:[ '-][A-Za-z]+)*$",
    "Use letters, spaces, hyphens, or apostrophes only.",
)

pakistani_phone = RegexValidator(
    r"^92\d{10}$",
    "Enter a valid phone number starting with 92 followed by 10 digits.",
)

six_digit_code = RegexValidator(
    r"^[0-9]{4,6}$",
    "Enter a valid postal code.",
)

cnic_format = RegexValidator(
    r"^\d{5}-\d{7}-\d$",
    "Format: 12345-1234567-1.",
)

passport_format = RegexValidator(
    r"^[A-Za-z]{1,2}[0-9]{6,7}$",
    "Enter a valid passport number, e.g. AB1234567.",
)

address_line_validator = RegexValidator(
    r"^[A-Za-z0-9][A-Za-z0-9\s,\-/#.]*$",
    "Enter a valid address (letters, numbers, and , - / # . only).",
)

institute_name_validator = RegexValidator(
    r"^[A-Za-z0-9][A-Za-z0-9&.,'\-\s]*$",
    "Enter a valid name.",
)

# Alphanumeric reference / transaction numbers (bank slips, NTS roll
# numbers, etc). These legitimately mix letters and digits, so they get
# their own validator rather than reusing a "name" validator.
alphanumeric_reference_validator = RegexValidator(
    r"^[A-Za-z0-9\-/]+$",
    "Use letters, numbers, hyphens, and slashes only.",
)


# ---------------------------------------------------------------------------
# Shared choices
# ---------------------------------------------------------------------------
SECTION_STATUS_CHOICES = [
    ("not_started", "Not Started"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("needs_correction", "Needs Correction"),
]

NATIONALITY_CHOICES = [
    ("Pakistani", "Pakistani"),
    ("Other", "Other"),
]

RELIGION_CHOICES = [
    ("Islam", "Islam"),
    ("Christianity", "Christianity"),
    ("Hinduism", "Hinduism"),
    ("Sikhism", "Sikhism"),
    ("Other", "Other"),
]

PROVINCE_CHOICES = [
    ("Punjab", "Punjab"),
    ("Sindh", "Sindh"),
    ("Khyber Pakhtunkhwa", "Khyber Pakhtunkhwa"),
    ("Balochistan", "Balochistan"),
    ("Gilgit-Baltistan", "Gilgit-Baltistan"),
    ("Azad Jammu & Kashmir", "Azad Jammu & Kashmir"),
    ("Islamabad Capital Territory", "Islamabad Capital Territory"),
]

GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
]

YES_NO_CHOICES = [
    ("yes", "Yes"),
    ("no", "No"),
]

DEGREE_CHOICES = [
    ("matric", "Matric / SSC"),
    ("intermediate", "Intermediate / A-Level"),
    ("bachelor", "Bachelor's"),
    ("master", "Master's"),
    ("other", "Other"),
]

STUDY_GROUP_CHOICES = [
    ("pre_medical", "Pre-Medical"),
    ("pre_engineering", "Pre-Engineering"),
    ("computer_science", "Computer Science"),
    ("commerce", "Commerce"),
    ("arts_humanities", "Arts / Humanities"),
    ("general_science", "General Science"),
    ("other", "Other"),
]

# Placeholder list of offered programs. Replace with a real Program model /
# DB-driven queryset once the institution's program catalogue is finalised;
# kept as static choices for now so the field still can't be typed freely.
PROGRAM_CHOICES = [
    ("bs_computer_science", "BS Computer Science"),
    ("bs_software_engineering", "BS Software Engineering"),
    ("bs_electrical_engineering", "BS Electrical Engineering"),
    ("bs_business_administration", "BS Business Administration"),
    ("bs_accounting_finance", "BS Accounting & Finance"),
    ("bs_english", "BS English"),
    ("bs_psychology", "BS Psychology"),
    ("md_medicine", "MBBS"),
    ("other", "Other"),
]

ENTRY_TEST_OPTION_CHOICES = [
    ("need_to_appear", "Need to Appear in Test"),
    ("already_qualified", "Already Qualified Entrance Test"),
    ("exempted", "Exempted from Test"),
]

TEST_CENTER_CHOICES = [
    ("peshawar", "Peshawar"),
    ("lahore", "Lahore"),
    ("karachi", "Karachi"),
    ("islamabad", "Islamabad"),
    ("quetta", "Quetta"),
    ("multan", "Multan"),
    ("other", "Other"),
]

TEST_TYPE_CHOICES = [
    ("nts", "NTS"),
    ("ecat", "ECAT"),
    ("mcat", "MCAT"),
    ("sat", "SAT"),
    ("university_specific", "University-Specific Test"),
    ("other", "Other"),
]

ADMISSION_SCHEME_CHOICES = [
    ("open_merit", "Open Merit"),
    ("self_finance", "Self Finance"),
    ("special_quota", "Special Quota"),
    ("overseas_pakistani", "Overseas Pakistani"),
    ("other", "Other"),
]

PAYMENT_MODE_CHOICES = [
    ("bank_deposit", "Bank Deposit"),
    ("online_transfer", "Online Transfer"),
    ("easypaisa_jazzcash", "Easypaisa / JazzCash"),
    ("pay_order", "Pay Order / Demand Draft"),
    ("other", "Other"),
]


# ---------------------------------------------------------------------------
# Core Application
# ---------------------------------------------------------------------------
class Application(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ready", "Ready for Submission"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("action_required", "Action Required"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    applicant = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="application",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    declaration_accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Section I — everything the applicant fills in before "Confirm &
    # Submit". Section II (fee + references) and Section III (test center)
    # are handled separately below via their own status properties, since
    # they are post-submission / post-decision steps and shouldn't affect
    # whether Section I is ready to submit.
    SECTION_KEYS = [
        "personal_info_status",
        "contact_address_status",
        "academic_info_status",
        "program_preference_status",
        "admission_test_status",
        "admission_scheme_status",
        "employment_status",
        "form_submission_status",
        "processing_fee_status",
        "referee_information_status",
        "test_center_status",
    ]

    SECTION_LABELS = {
        "personal_info_status": "Personal Information",
        "contact_address_status": "Contact & Address",
        "academic_info_status": "Academic Information",
        "program_preference_status": "Program Preferences",
        "admission_test_status": "Admission Test",
        "admission_scheme_status": "Admission Scheme",
        "employment_status": "Current Employment",
        "form_submission_status": "Form Submission",
        "processing_fee_status": "Processing Fee",
        "referee_information_status": "References & LOR",
        "test_center_status": "Test Center",
    }

    def __str__(self):
        return f"Application: {self.applicant}"

    @property
    def personal_info_status(self):
        try:
            return self.personal_info.status
        except PersonalInfo.DoesNotExist:
            return "not_started"

    @property
    def contact_address_status(self):
        try:
            return self.contact_address.status
        except ContactAddress.DoesNotExist:
            return "not_started"

    @property
    def academic_info_status(self):
        try:
            return self.academic_info.status
        except AcademicInfo.DoesNotExist:
            return "not_started"

    @property
    def program_preference_status(self):
        try:
            return self.program_preference.status
        except ProgramPreference.DoesNotExist:
            return "not_started"

    @property
    def admission_test_status(self):
        try:
            return self.admission_test.status
        except AdmissionTest.DoesNotExist:
            return "not_started"

    @property
    def admission_scheme_status(self):
        try:
            return self.admission_scheme.status
        except AdmissionScheme.DoesNotExist:
            return "not_started"

    @property
    def employment_status(self):
        try:
            return self.current_employment.status
        except CurrentEmployment.DoesNotExist:
            return "not_started"

    @property
    def form_submission_status(self):
        try:
            return self.form_submission.status
        except FormSubmission.DoesNotExist:
            return "not_started"
        
    # -- Section II / III status (kept separate from SECTION_KEYS on
    # purpose — see the comment above SECTION_KEYS). --------------------
    @property
    def processing_fee_status(self):
        try:
            return self.processing_fee.status
        except ProcessingFee.DoesNotExist:
            return "not_started"

    @property
    def referee_information_status(self):
        try:
            return self.referee_information.status
        except RefereeInformation.DoesNotExist:
            return "not_started"

    @property
    def test_center_status(self):
        try:
            return self.test_center.status
        except TestCenter.DoesNotExist:
            return "not_started"

    @property
    def sections_completed_count(self):
        statuses = [
            getattr(self, key) for key in self.SECTION_KEYS
        ]

        return sum(status == "completed" for status in statuses)

    @property
    def sections_total(self):
        return len(self.SECTION_KEYS)

    @property
    def progress_percent(self):
        if not self.sections_total:
            return 0

        return int(
            round(
                (self.sections_completed_count / self.sections_total) * 100
            )
        )

    @property
    def checklist(self):
        status_labels = dict(SECTION_STATUS_CHOICES)

        items = []
        for key in self.SECTION_KEYS:
            status = getattr(self, key)
            items.append(
                {
                    "key": key,
                    "name": self.SECTION_LABELS[key],
                    "status_key": status.replace("_", ""),
                    "status_label": status_labels.get(status, status),
                }
            )

        return items

    @property
    def is_ready_for_submission(self):
        return (
            self.sections_completed_count == self.sections_total
            and self.status == "draft"
        )


# ---------------------------------------------------------------------------
# Section 1: Personal Information
# ---------------------------------------------------------------------------
class PersonalInfo(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="personal_info",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    student_photo = models.TextField(blank=True, null=True)
    student_photo_type = models.CharField(max_length=20, blank=True)

    full_name = models.CharField(
        max_length=100,
        validators=[letters_and_spaces],
    )

    father_name = models.CharField(
        max_length=100,
        validators=[letters_and_spaces],
    )

    guardian_name = models.CharField(
        max_length=100,
        validators=[letters_and_spaces],
        blank=True,
    )

    guardian_contact_no = models.CharField(
        "Father / Guardian Contact No.",
        max_length=12,
        validators=[pakistani_phone],
    )

    cell_no = models.CharField(
        max_length=12,
        validators=[pakistani_phone],
    )

    religion = models.CharField(
        max_length=50,
        choices=RELIGION_CHOICES,
    )

    date_of_birth = models.DateField()

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
    )

    nationality = models.CharField(
        max_length=50,
        choices=NATIONALITY_CHOICES,
        default="Pakistani",
    )

    cnic = models.CharField(
        "CNIC / B-Form Number",
        max_length=15,
        validators=[cnic_format],
        unique=True,
        blank=True,
        null=True,
    )

    passport_no = models.CharField(
        max_length=20,
        validators=[passport_format],
        blank=True,
        null=True,
        help_text="Only applicable if nationality is not Pakistani.",
    )

    domicile_province = models.CharField(
        max_length=30,
        choices=PROVINCE_CHOICES,
    )

    domicile_district = models.CharField(
        max_length=50,
        validators=[letters_and_spaces],
    )

    disability_status = models.CharField(
        "Do you have any disability?",
        max_length=3,
        choices=YES_NO_CHOICES,
    )

    def clean(self):
        errors = {}

        if self.nationality == "Pakistani":
            if not self.cnic:
                errors["cnic"] = "CNIC is required for Pakistani nationals."
            if self.passport_no:
                errors["passport_no"] = (
                    "Passport number should only be provided for "
                    "non-Pakistani nationals."
                )
        else:
            if not self.passport_no:
                errors["passport_no"] = (
                    "Passport number is required for non-Pakistani "
                    "nationals."
                )
            if self.cnic:
                errors["cnic"] = (
                    "CNIC should only be provided for Pakistani nationals."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"PersonalInfo: {self.application}"


# ---------------------------------------------------------------------------
# Section 2: Contact & Address
# ---------------------------------------------------------------------------
class ContactAddress(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="contact_address",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    mailing_same_as_permanent = models.BooleanField(
        default=False,
        help_text="If checked, mailing address is copied from the "
        "permanent address.",
    )

    # --- Permanent Address ---
    permanent_house_street_no = models.CharField(
        "House No. & Street No.",
        max_length=100,
        validators=[address_line_validator],
    )

    permanent_mohalla_tehsil = models.CharField(
        "Mohalla / Village / Tehsil",
        max_length=100,
        validators=[letters_and_spaces],
    )

    permanent_district = models.CharField(
        max_length=50,
        validators=[letters_and_spaces],
    )

    permanent_city = models.CharField(
        max_length=50,
        validators=[letters_and_spaces],
    )

    permanent_phone = models.CharField(
        max_length=12,
        validators=[pakistani_phone],
    )

    permanent_courier_available = models.BooleanField(
        null=True,
        blank=True,
    )

    # --- Mailing Address ---
    mailing_house_street_no = models.CharField(
        "House No. & Street No.",
        max_length=100,
        validators=[address_line_validator],
        blank=True,
    )

    mailing_mohalla_tehsil = models.CharField(
        "Mohalla / Village / Tehsil",
        max_length=100,
        validators=[letters_and_spaces],
        blank=True,
    )

    mailing_district = models.CharField(
        max_length=50,
        validators=[letters_and_spaces],
        blank=True,
    )

    mailing_city = models.CharField(
        max_length=50,
        validators=[letters_and_spaces],
        blank=True,
    )

    mailing_phone = models.CharField(
        max_length=12,
        validators=[pakistani_phone],
        blank=True,
    )

    mailing_courier_available = models.BooleanField(
        null=True,
        blank=True,
    )

    def clean(self):
        if self.mailing_same_as_permanent:
            self.mailing_house_street_no = self.permanent_house_street_no
            self.mailing_mohalla_tehsil = self.permanent_mohalla_tehsil
            self.mailing_district = self.permanent_district
            self.mailing_city = self.permanent_city
            self.mailing_phone = self.permanent_phone
            self.mailing_courier_available = self.permanent_courier_available
            return

        required_fields = [
            "mailing_house_street_no",
            "mailing_mohalla_tehsil",
            "mailing_district",
            "mailing_city",
            "mailing_phone",
        ]

        errors = {
            field: "This field is required unless 'same as permanent "
            "address' is checked."
            for field in required_fields
            if not getattr(self, field)
        }

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"ContactAddress: {self.application}"


# ---------------------------------------------------------------------------
# Section 3: Previous / Academic Education
# ---------------------------------------------------------------------------
class AcademicInfo(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="academic_info",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    degree_certificate = models.CharField(
        "Degree / Certificate",
        max_length=20,
        choices=DEGREE_CHOICES,
    )

    board_university = models.CharField(
        "Board / University",
        max_length=150,
        validators=[institute_name_validator],
    )

    degree_title = models.CharField(
        max_length=150,
        validators=[institute_name_validator],
    )

    institute_name = models.CharField(
        max_length=150,
        validators=[institute_name_validator],
    )

    obtained_marks = models.DecimalField(
        "Obtained Marks / CGPA",
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    total_marks = models.DecimalField(
        "Total Marks / Scale (for CGPA)",
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    passing_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1950), MaxValueValidator(2035)],
    )

    study_group = models.CharField(
        max_length=30,
        choices=STUDY_GROUP_CHOICES,
    )

    country_studied = models.CharField(
        max_length=50,
        validators=[letters_and_spaces],
        default="Pakistan",
    )

    result_declared = models.CharField(
        max_length=3,
        choices=YES_NO_CHOICES,
    )

    def clean(self):
        if (
            self.obtained_marks is not None
            and self.total_marks is not None
            and self.obtained_marks > self.total_marks
        ):
            raise ValidationError(
                {
                    "obtained_marks": "Obtained marks/CGPA cannot exceed "
                    "total marks/scale."
                }
            )

    def __str__(self):
        return f"AcademicInfo: {self.application}"


# ---------------------------------------------------------------------------
# Section 4: Program Preferences
# ---------------------------------------------------------------------------
class ProgramPreference(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="program_preference",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    program_choice = models.CharField(
        max_length=50,
        choices=PROGRAM_CHOICES,
    )

    def __str__(self):
        return f"ProgramPreference: {self.application}"


# ---------------------------------------------------------------------------
# Section 5: Admission Test
# ---------------------------------------------------------------------------
class AdmissionTest(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="admission_test",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    entry_test_option = models.CharField(
        max_length=20,
        choices=ENTRY_TEST_OPTION_CHOICES,
    )

    test_center = models.CharField(
        max_length=20,
        choices=TEST_CENTER_CHOICES,
    )

    # --- Only required when entry_test_option == "already_qualified" ---
    test_center_name = models.CharField(
        max_length=150,
        validators=[institute_name_validator],
        blank=True,
    )

    test_type = models.CharField(
        max_length=30,
        choices=TEST_TYPE_CHOICES,
        blank=True,
    )

    obtained_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )

    total_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
    )

    date_of_test = models.DateField(blank=True, null=True)

    # Evidence document, same base64-in-TextField pattern as
    # PersonalInfo.student_photo — the view is responsible for writing to
    # this field; keep it out of any ModelForm's Meta.fields.
    evidence_document = models.TextField(blank=True, null=True)
    evidence_document_type = models.CharField(max_length=20, blank=True)

    def clean(self):
        if self.entry_test_option != "already_qualified":
            return

        errors = {}
        required_fields = [
            "test_center_name",
            "test_type",
            "obtained_marks",
            "total_marks",
            "date_of_test",
        ]
        for field in required_fields:
            if not getattr(self, field):
                errors[field] = (
                    "This field is required when you have already "
                    "qualified the entrance test."
                )

        if not self.evidence_document:
            errors["evidence_document"] = (
                "Please upload evidence of your qualified test result."
            )

        if (
            self.obtained_marks is not None
            and self.total_marks is not None
            and self.obtained_marks > self.total_marks
        ):
            errors["obtained_marks"] = (
                "Obtained marks cannot exceed total marks."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"AdmissionTest: {self.application}"


# ---------------------------------------------------------------------------
# Section 6: Admission Scheme
# ---------------------------------------------------------------------------
class AdmissionScheme(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="admission_scheme",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    admission_scheme = models.CharField(
        "Admission Scheme",
        max_length=30,
        choices=ADMISSION_SCHEME_CHOICES,
    )

    ga_ship_interest = models.BooleanField(
        "GA-ship Interest",
        null=True,
        blank=True,
    )

    day_scholar_interest = models.BooleanField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"AdmissionScheme: {self.application}"


# ---------------------------------------------------------------------------
# Section 7: Current Employment
# ---------------------------------------------------------------------------
class CurrentEmployment(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="current_employment",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    no_employment_history = models.BooleanField(default=False)

    # --- Only required when no_employment_history is False ---
    employer = models.CharField(
        max_length=150,
        validators=[institute_name_validator],
        blank=True,
    )

    job_title = models.CharField(
        max_length=100,
        validators=[letters_and_spaces],
        blank=True,
    )

    date_of_joining = models.DateField(blank=True, null=True)

    still_working_here = models.BooleanField(null=True, blank=True)

    def clean(self):
        if self.no_employment_history:
            return

        errors = {}
        for field in ["employer", "job_title", "date_of_joining"]:
            if not getattr(self, field):
                errors[field] = (
                    "This field is required unless 'No Employment "
                    "History' is checked."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"CurrentEmployment: {self.application}"


# ---------------------------------------------------------------------------
# 8. Form Submission
# ---------------------------------------------------------------------------

class FormSubmission(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="form_submission",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    declaration_accepted = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"FormSubmission: {self.application}"

# ---------------------------------------------------------------------------
# SECTION II
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 9. Processing Fee
# ---------------------------------------------------------------------------
class ProcessingFee(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="processing_fee",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    bank_provider_name = models.CharField(
        max_length=150,
        validators=[institute_name_validator],
    )

    payment_mode = models.CharField(
        max_length=30,
        choices=PAYMENT_MODE_CHOICES,
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    reference_number = models.CharField(
        max_length=50,
        validators=[alphanumeric_reference_validator],
    )

    # Base64-in-TextField pattern, same as PersonalInfo.student_photo.
    proof_of_payment = models.TextField(blank=True, null=True)
    proof_of_payment_type = models.CharField(max_length=20, blank=True)

    fee_deposited = models.BooleanField(default=False)

    def __str__(self):
        return f"ProcessingFee: {self.application}"


# ---------------------------------------------------------------------------
# 10. References & LOR
# ---------------------------------------------------------------------------
class RefereeInformation(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="referee_information",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    referee_name = models.CharField(
        max_length=100,
        validators=[letters_and_spaces],
    )

    contact_number = models.CharField(
        max_length=12,
        validators=[pakistani_phone],
    )

    email = models.EmailField()

    university_name = models.CharField(
        max_length=150,
        validators=[institute_name_validator],
    )

    designation = models.CharField(
        max_length=100,
        validators=[letters_and_spaces],
    )

    # Base64-in-TextField pattern, same as PersonalInfo.student_photo.
    recommendation_letter = models.TextField(blank=True, null=True)
    recommendation_letter_type = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"RefereeInformation: {self.application}"


# ---------------------------------------------------------------------------
# SECTION III
# 11. Test Center
#
# The required fields for this section weren't visible in the provided
# screenshot, so only a status-tracked stub is created here. Add the real
# fields (with the same letters-only / phone-only / org-name validator
# pattern used above) once they're confirmed, then remember to also:
#   - add "test_center_status" to Application if it should gate submission
#   - add a TestCenterForm in forms.py
# ---------------------------------------------------------------------------
class TestCenter(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="test_center",
    )

    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS_CHOICES,
        default="not_started",
    )

    def __str__(self):
        return f"TestCenter: {self.application}"