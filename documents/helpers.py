"""
documents/helpers.py
Helper functions shared between documents and applications apps.
Placed here to avoid cross-app view imports.
"""
from applications.models import DocumentsSummary
from .models import Document


def required_document_types(application):
    required = ["cnic_bform", "father_cnic", "matric_certificate", "domicile_certificate"]
    if application.intermediate_result != "awaited":
        required.append("intermediate_certificate")
    return required


def update_documents_status(application):
    required = required_document_types(application)
    uploaded = set(
        application.documents.filter(file__isnull=False)
        .exclude(file="")
        .values_list("doc_type", flat=True)
    )
    status = "completed" if all(dt in uploaded for dt in required) else "not_started"
    summary, _ = DocumentsSummary.objects.get_or_create(application=application)
    summary.documents_status = status
    summary.save(update_fields=["documents_status"])
