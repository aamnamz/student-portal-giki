from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from applications.models import Application

from .models import Document


def required_document_types(application):
    required = ["cnic_bform", "father_cnic", "matric_certificate", "domicile_certificate"]
    if application.intermediate_result != "awaited":
        required.append("intermediate_certificate")
    return required


def update_documents_status(application):
    required = required_document_types(application)
    uploaded = set(application.documents.filter(file__isnull=False).exclude(file="").values_list("doc_type", flat=True))
    application.documents_status = "completed" if all(doc_type in uploaded for doc_type in required) else "not_started"
    application.save(update_fields=["documents_status", "updated_at"])


@login_required
def documents(request):
    application, _ = Application.objects.get_or_create(applicant=request.user)

    # Make sure a Document row exists for every required doc type,
    # so the page always shows all 5 rows even before anything's uploaded.
    required_types = required_document_types(application)
    existing_types = set(application.documents.values_list("doc_type", flat=True))
    for doc_type, _label in Document.DOC_TYPES:
        if doc_type not in existing_types:
            Document.objects.create(application=application, doc_type=doc_type)

    if request.method == "POST":
        document = application.documents.filter(pk=request.POST.get("document_id")).first()
        uploaded_file = request.FILES.get("file")
        if document and uploaded_file:
            document.file = uploaded_file
            document.status = "uploaded"
            document.uploaded_at = timezone.now()
            document.save()
            update_documents_status(application)
        return redirect("documents")

    update_documents_status(application)

    return render(request, "documents/documents.html", {
        "active_nav": "application",
        "documents": application.documents.filter(doc_type__in=required_types),
    })
