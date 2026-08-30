from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from applications.models import Application
from .helpers import required_document_types, update_documents_status
from .models import Document


def required_document_types(application):
    """Determine required documents based on academic info."""
    required = ["cnic_bform", "father_cnic", "matric_certificate", "domicile_certificate"]
    
    # Check if intermediate result is awaited
    try:
        if application.academic_info.intermediate_result != "awaited":
            required.append("intermediate_certificate")
    except:
        # academic_info doesn't exist yet
        pass
    
    return required


def update_documents_status(application):
    """Update the Application's documents_status based on Document objects.
    This is called after academic info is completed."""
    from applications.models import Document as AppDocument
    
    required = required_document_types(application)
    uploaded = set(application.documents.filter(file__isnull=False).exclude(file="").values_list("doc_type", flat=True))
    
    # documents_status is a @property, so we can't set it directly
    # But the property is computed from Document objects, so just ensure
    # the documents exist in the database
    required_types = required_document_types(application)
    existing_types = set(application.documents.values_list("doc_type", flat=True))
    for doc_type, _label in Document.DOC_TYPES:
        if doc_type not in existing_types:
            Document.objects.create(application=application, doc_type=doc_type)


@login_required
def documents(request):
    application = Application.objects.filter(applicant=request.user).first()
    if not application:
        application = Application.objects.create(applicant=request.user)

    required_types = required_document_types(application)

    # Ensure a Document row exists for every required type
    existing_types = set(application.documents.values_list("doc_type", flat=True))
    for doc_type, _label in Document.DOC_TYPES:
        if doc_type not in existing_types:
            Document.objects.create(application=application, doc_type=doc_type)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "save_declaration":
            accepted = request.POST.get("declaration_accepted") == "on"
            application.declaration_accepted = accepted
            application.save(update_fields=["declaration_accepted", "updated_at"])
            if accepted:
                return redirect("review_application")
            return redirect("documents")

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
        "application": application,
        "documents": application.documents.filter(doc_type__in=required_types),
    })
