from django.conf import settings
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models


letters_only = RegexValidator(r"^[A-Za-z]+(?:[-'][A-Za-z]+)*$", "Use letters only.")
letters_and_spaces = RegexValidator(r"^[A-Za-z]+(?:[ '-][A-Za-z]+)*$", "Use letters, spaces, hyphens, or apostrophes only.")
ten_digit_phone = RegexValidator(r'^\d{10}$', 'Enter a valid 10 digit mobile number.')
six_digit_code = RegexValidator(r'^[0-9]{4,6}$', 'Enter a valid postal code.')
cnic_format = RegexValidator(r'^\d{5}-\d{7}-\d$', 'Format: 12345-1234567-1.')

SECTION_STATUS_CHOICES = [
    ("not_started", "Not Started"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("needs_correction", "Needs Correction"),
]

NATIONALITY_CHOICES = [
        ('Pakistani', 'Pakistani'),
        ('Other', 'Other'),
    ]

RELIGION_CHOICES = [
        ('Islam', 'Islam'),
        ('Christianity', 'Christianity'),
        ('Hinduism', 'Hinduism'),
        ('Sikhism', 'Sikhism'),
        ('Other', 'Other'),
    ]

PROVINCE_CHOICES = [
        ('Punjab', 'Punjab'),
        ('Sindh', 'Sindh'),
        ('Khyber Pakhtunkhwa', 'Khyber Pakhtunkhwa'),
        ('Balochistan', 'Balochistan'),
        ('Gilgit-Baltistan', 'Gilgit-Baltistan'),
        ('Azad Jammu & Kashmir', 'Azad Jammu & Kashmir'),
        ('Islamabad Capital Territory', 'Islamabad Capital Territory'),
    ]

class Application(models.Model):
    """
    One Application per applicant. Holds the data for all 5 form
    sections plus a per-section status, so the dashboard checklist
    and progress ring can be computed directly from this model.
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ready", "Ready for Submission"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("action_required", "Action Required"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("other", "Other")]

    applicant = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="application"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # ---- Section 1: Personal Information ----
    personal_info_status = models.CharField(max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started")
    full_name = models.CharField(max_length=150, blank=True)
    student_photo = models.TextField(blank=True, null=True)
    student_photo_type = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=30, validators=[letters_only])
    last_name = models.CharField(max_length=30, validators=[letters_only])
    father_name = models.CharField(max_length=50, validators=[letters_and_spaces])
    mother_name = models.CharField(max_length=50, validators=[letters_and_spaces], blank=True)
    cnic_or_bform = models.CharField(
        "CNIC / B-Form Number",
        max_length=15,
        validators=[cnic_format],
        unique=True,
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=50, blank=True, default="Pakistani")
    blood_group = models.CharField(max_length=5, blank=True)
    marital_status = models.CharField(max_length=12, blank=True)

    # ---- Section 2: Contact & Address ----
    contact_address_status = models.CharField(max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started")
    phone = models.CharField(max_length=10, validators=[ten_digit_phone], blank=True)
    alternate_phone = models.CharField(max_length=10, validators=[ten_digit_phone], blank=True)
    email_address = models.EmailField(unique=True, max_length=100)
    permanent_address = models.TextField(max_length=200)
    present_address = models.TextField(max_length=200)
    city = models.CharField(max_length=30, validators=[letters_and_spaces])
    province = models.CharField(max_length=30, choices=PROVINCE_CHOICES)
    postal_code = models.CharField(max_length=6, validators=[six_digit_code])
    district = models.CharField(max_length=30, validators=[letters_and_spaces])
    domicile_province = models.CharField(max_length=30, choices=PROVINCE_CHOICES)
    domicile_district = models.CharField(max_length=30, validators=[letters_and_spaces])

    # ---- Section 3: Academic Information ----
    academic_info_status = models.CharField(max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started")
    matric_board = models.CharField("Matric Group", max_length=150, blank=True)
    matric_year = models.PositiveIntegerField(null=True, blank=True)
    matric_marks = models.PositiveIntegerField(null=True, blank=True)
    matric_total_marks = models.PositiveIntegerField(null=True, blank=True)
    matric_grade = models.CharField(max_length=20, blank=True)
    intermediate_board = models.CharField("Intermediate / A-Level Board", max_length=150, blank=True)
    intermediate_year = models.PositiveIntegerField(null=True, blank=True)
    intermediate_marks = models.PositiveIntegerField(null=True, blank=True)
    intermediate_total_marks = models.PositiveIntegerField(null=True, blank=True)
    intermediate_group = models.CharField(max_length=50, blank=True)
    intermediate_grade = models.CharField(max_length=20, blank=True)
    intermediate_result = models.CharField(max_length=20, blank=True)
    entry_test_score = models.CharField(max_length=50, blank=True)
    degree_program = models.CharField(max_length=100, blank=True)

    # ---- Section 4: Guardian Information ----
    guardian_info_status = models.CharField(max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started")
    guardian_name = models.CharField(max_length=150, validators=[letters_and_spaces], blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_cnic = models.CharField(max_length=15, validators=[cnic_format], blank=True)
    guardian_occupation = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=10, validators=[ten_digit_phone], blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_address = models.TextField(blank=True)
    guardian_income = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=150, validators=[letters_and_spaces], blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    emergency_contact_number = models.CharField(max_length=10, validators=[ten_digit_phone], blank=True)

    # ---- Section 5: Documents (status rolls up from Document objects below) ----
    documents_status = models.CharField(max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started")
    additional_info_status = models.CharField(max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started")
    hostel_required = models.BooleanField(null=True, blank=True)
    scholarship_required = models.BooleanField(null=True, blank=True)
    disability_status = models.BooleanField(null=True, blank=True)
    declaration_accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    SECTION_KEYS = [
        "personal_info_status",
        "contact_address_status",
        "academic_info_status",
        "guardian_info_status",
        "documents_status",
        "additional_info_status",
    ]
    SECTION_LABELS = {
        "personal_info_status": "Personal Information",
        "contact_address_status": "Contact & Address",
        "academic_info_status": "Academic Information",
        "guardian_info_status": "Guardian Information",
        "documents_status": "Documents",
        "additional_info_status": "Additional Information",
    }

    def __str__(self):
        return f"Application: {self.applicant}"

    @property
    def sections_completed_count(self):
        return sum(1 for key in self.SECTION_KEYS if getattr(self, key) == "completed")

    @property
    def sections_total(self):
        return len(self.SECTION_KEYS)

    @property
    def progress_percent(self):
        if not self.sections_total:
            return 0
        return int(round((self.sections_completed_count / self.sections_total) * 100))

    @property
    def checklist(self):
        """List of dicts the dashboard/overview templates can loop over directly."""
        return [
            {
                "key": key,
                "name": self.SECTION_LABELS[key],
                "status_key": getattr(self, key).replace("_", ""),
                "status_label": dict(SECTION_STATUS_CHOICES)[getattr(self, key)],
            }
            for key in self.SECTION_KEYS
        ]

    @property
    def is_ready_for_submission(self):
        return self.sections_completed_count == self.sections_total and self.status == "draft"
