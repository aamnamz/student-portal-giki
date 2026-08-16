from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("application", "doc_type", "status", "uploaded_at", "reviewed_at")
    list_filter = ("doc_type", "status")
    search_fields = ("application__applicant__username", "application__full_name")
