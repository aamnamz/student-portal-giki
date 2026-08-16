from django.contrib import admin

from .models import AdmissionCycle, Notice


@admin.register(AdmissionCycle)
class AdmissionCycleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "application_deadline", "document_deadline",
                     "entry_test_date", "interview_date", "decision_date")
    list_filter = ("is_active",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "notice_type", "applicant", "created_at")
    list_filter = ("notice_type",)
