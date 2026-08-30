from django.conf import settings
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models


letters_only = RegexValidator(r"^[A-Za-z]+(?:[-'][A-Za-z]+)*$", "Use letters only.")
letters_and_spaces = RegexValidator(r"^[A-Za-z]+(?:[ '-][A-Za-z]+)*$", "Use letters, spaces, hyphens, or apostrophes only.")
pakistani_phone = RegexValidator(
    r'^92\d{10}$',
    'Enter a valid phone number starting with 92 followed by 10 digits.',
)
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
    Root application object that tracks overall status and timestamps.
    Application-specific data is split into separate Section models.
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

    applicant = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="application"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
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
        count = 0
        if self.personal_info.status == "completed":
            count += 1
        if self.contact_address.status == "completed":
            count += 1
        if self.academic_info.status == "completed":
            count += 1
        if self.guardian_info.status == "completed":
            count += 1
        if self.additional_info.status == "completed":
            count += 1
        # Documents status is computed separately
        if self.documents_status == "completed":
            count += 1
        return count

    @property
    def sections_total(self):
        return len(self.SECTION_KEYS)

    @property
    def progress_percent(self):
        if not self.sections_total:
            return 0
        return int(round((self.sections_completed_count / self.sections_total) * 100))

    @property
    def documents_status(self):
        """Computed from Document model objects."""
        from documents.models import Document
        docs = Document.objects.filter(application=self)
        if not docs.exists():
            return "not_started"
        if all(doc.status == "verified" for doc in docs):
            return "completed"
        if any(doc.status == "rejected" for doc in docs):
            return "needs_correction"
        if any(doc.status in ["under_verification", "uploaded"] for doc in docs):
            return "in_progress"
        return "not_started"

    @property
    def checklist(self):
        """List of dicts the dashboard/overview templates can loop over directly."""
        sections_data = [
            {"key": "personal_info_status", "status": self.personal_info.status},
            {"key": "contact_address_status", "status": self.contact_address.status},
            {"key": "academic_info_status", "status": self.academic_info.status},
            {"key": "guardian_info_status", "status": self.guardian_info.status},
            {"key": "additional_info_status", "status": self.additional_info.status},
            {"key": "documents_status", "status": self.documents_status},
        ]
        
        return [
            {
                "key": section["key"],
                "name": self.SECTION_LABELS[section["key"]],
                "status_key": section["status"].replace("_", ""),
                "status_label": dict(SECTION_STATUS_CHOICES)[section["status"]],
            }
            for section in sections_data
        ]

    @property
    def is_ready_for_submission(self):
        return self.sections_completed_count == self.sections_total and self.status == "draft"


class PersonalInfo(models.Model):
    """Section 1: Personal Information"""
    
    GENDER_CHOICES = [("male", "Male"), ("female", "Female"), ("other", "Other")]
    
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="personal_info"
    )
    status = models.CharField(
        max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started"
    )
    
    # Personal data
    student_photo = models.TextField(blank=True, null=True)  # base64 encoded
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Personal Information'
        verbose_name_plural = 'Personal Information'

    def __str__(self):
        return f"Personal Info: {self.application.applicant}"

    @property
    def full_name(self):
        """Computed property - no database column needed."""
        return f"{self.first_name} {self.last_name}".strip()


class ContactAddress(models.Model):
    """Section 2: Contact & Address Information"""
    
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="contact_address"
    )
    status = models.CharField(
        max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started"
    )
    
    # Contact & Address data
    phone = models.CharField(max_length=12, validators=[pakistani_phone], blank=True)
    alternate_phone = models.CharField(max_length=12, validators=[pakistani_phone], blank=True)
    permanent_address = models.TextField(max_length=200)
    present_address = models.TextField(max_length=200)
    city = models.CharField(max_length=30, validators=[letters_and_spaces])
    province = models.CharField(max_length=30, choices=PROVINCE_CHOICES)
    postal_code = models.CharField(max_length=6, validators=[six_digit_code])
    district = models.CharField(max_length=30, validators=[letters_and_spaces])
    domicile_province = models.CharField(max_length=30, choices=PROVINCE_CHOICES)
    domicile_district = models.CharField(max_length=30, validators=[letters_and_spaces])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contact & Address'
        verbose_name_plural = 'Contact & Addresses'

    def __str__(self):
        return f"Contact & Address: {self.application.applicant}"


class AcademicInfo(models.Model):
    """Section 3: Academic Information"""
    
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="academic_info"
    )
    status = models.CharField(
        max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started"
    )
    
    # Academic data
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Academic Information'
        verbose_name_plural = 'Academic Information'

    def __str__(self):
        return f"Academic Info: {self.application.applicant}"


class GuardianInfo(models.Model):
    """Section 4: Guardian Information"""
    
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="guardian_info"
    )
    status = models.CharField(
        max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started"
    )
    
    # Guardian data
    guardian_name = models.CharField(max_length=150, validators=[letters_and_spaces], blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_cnic = models.CharField(max_length=15, validators=[cnic_format], blank=True)
    guardian_occupation = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=12, validators=[pakistani_phone], blank=True)
    guardian_email = models.EmailField(blank=True)
    guardian_address = models.TextField(blank=True)
    guardian_income = models.CharField(max_length=50, blank=True)
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=150, validators=[letters_and_spaces], blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    emergency_contact_number = models.CharField(max_length=12, validators=[pakistani_phone], blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Guardian Information'
        verbose_name_plural = 'Guardian Information'

    def __str__(self):
        return f"Guardian Info: {self.application.applicant}"


class AdditionalInfo(models.Model):
    """Section 5: Additional Information & Preferences"""
    
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="additional_info"
    )
    status = models.CharField(
        max_length=20, choices=SECTION_STATUS_CHOICES, default="not_started"
    )
    
    # Additional preferences
    hostel_required = models.BooleanField(null=True, blank=True)
    scholarship_required = models.BooleanField(null=True, blank=True)
    disability_status = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Additional Information'
        verbose_name_plural = 'Additional Information'

    def __str__(self):
        return f"Additional Info: {self.application.applicant}"
