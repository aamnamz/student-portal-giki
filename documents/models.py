from django.db import models


class Document(models.Model):
    DOC_TYPES = [
        ("cnic_bform", "CNIC Copy"),
        ("father_cnic", "Father's CNIC Copy"),
        ("matric_certificate", "Matric Certificate"),
        ("intermediate_certificate", "Intermediate Certificate"),
        ("domicile_certificate", "Domicile Certificate"),
    ]
    STATUS_CHOICES = [
        ("not_uploaded", "Not Uploaded"),
        ("uploaded", "Uploaded"),
        ("under_verification", "Under Verification"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
        ("replace_required", "Replace Required"),
    ]

    # String reference "applications.Application" avoids a circular import
    # between the applications and documents apps.
    application = models.ForeignKey(
        "applications.Application", on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES)
    file = models.FileField(upload_to="documents/%Y/%m/", blank=True, null=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="not_uploaded")
    rejection_reason = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("application", "doc_type")

    def __str__(self):
        return f"{self.get_doc_type_display()} — {self.application.applicant}"
