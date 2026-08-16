from django.contrib import admin

from documents.models import Document

from .models import Application


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "status", "progress_percent", "sections_completed_count", "updated_at")
    list_filter = ("status",)
    search_fields = ("applicant__username", "applicant__first_name", "applicant__last_name", "full_name")
    inlines = [DocumentInline]
    fieldsets = (
        ("Status", {"fields": ("applicant", "status")}),
        ("Personal Information", {
            "fields": ("personal_info_status", "full_name", "father_name", "cnic_or_bform",
                       "date_of_birth", "gender", "religion", "nationality"),
        }),
        ("Contact & Address", {
            "fields": ("contact_address_status", "phone", "permanent_address",
                       "present_address", "city", "province", "postal_code"),
        }),
        ("Academic Information", {
            "fields": ("academic_info_status", "matric_board", "matric_year", "matric_marks",
                       "matric_total_marks", "intermediate_board", "intermediate_year",
                       "intermediate_marks", "intermediate_total_marks", "entry_test_score"),
        }),
        ("Guardian Information", {
            "fields": ("guardian_info_status", "guardian_name", "guardian_relationship", "guardian_cnic",
                       "guardian_occupation", "guardian_phone", "guardian_email", "guardian_address"),
        }),
        ("Documents", {"fields": ("documents_status",)}),
        ("Timestamps", {"fields": ("submitted_at",)}),
    )
