from django.contrib import admin

from documents.models import Document

from .models import Application, PersonalInfo, ContactAddress, AcademicInfo, GuardianInfo, AdditionalInfo


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


class PersonalInfoInline(admin.TabularInline):
    model = PersonalInfo
    extra = 0
    fields = ("status", "first_name", "last_name", "cnic_or_bform", "gender")


class ContactAddressInline(admin.TabularInline):
    model = ContactAddress
    extra = 0
    fields = ("status", "phone", "city", "province")


class AcademicInfoInline(admin.TabularInline):
    model = AcademicInfo
    extra = 0
    fields = ("status", "matric_board", "intermediate_board")


class GuardianInfoInline(admin.TabularInline):
    model = GuardianInfo
    extra = 0
    fields = ("status", "guardian_name", "guardian_phone")


class AdditionalInfoInline(admin.TabularInline):
    model = AdditionalInfo
    extra = 0
    fields = ("status", "hostel_required", "scholarship_required", "disability_status")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "status", "progress_percent", "sections_completed_count", "updated_at")
    list_filter = ("status",)
    search_fields = ("applicant__username", "applicant__first_name", "applicant__last_name")
    readonly_fields = ("progress_percent", "sections_completed_count", "created_at", "updated_at")
    inlines = [PersonalInfoInline, ContactAddressInline, AcademicInfoInline, GuardianInfoInline, AdditionalInfoInline, DocumentInline]
    fieldsets = (
        ("Status", {"fields": ("applicant", "status", "declaration_accepted")}),
        ("Progress", {"fields": ("progress_percent", "sections_completed_count")}),
        ("Timestamps", {"fields": ("submitted_at", "created_at", "updated_at")}),
    )


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "full_name", "cnic_or_bform")
    list_filter = ("status",)
    search_fields = ("application__applicant__username", "first_name", "last_name", "cnic_or_bform")
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Personal Information", {
            "fields": ("first_name", "last_name", "father_name", "mother_name", "cnic_or_bform",
                       "date_of_birth", "gender", "religion", "nationality", "blood_group", "marital_status"),
        }),
        ("Photo", {"fields": ("student_photo_type",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(ContactAddress)
class ContactAddressAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "phone", "city", "province")
    list_filter = ("status", "province")
    search_fields = ("application__applicant__username", "phone", "city")
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Contact", {"fields": ("phone", "alternate_phone")}),
        ("Present Address", {"fields": ("present_address", "city", "district", "province", "postal_code")}),
        ("Permanent Address", {"fields": ("permanent_address",)}),
        ("Domicile", {"fields": ("domicile_province", "domicile_district")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(AcademicInfo)
class AcademicInfoAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "matric_board", "intermediate_board")
    list_filter = ("status",)
    search_fields = ("application__applicant__username",)
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Matric", {
            "fields": ("matric_board", "matric_year", "matric_marks", "matric_total_marks", "matric_grade"),
        }),
        ("Intermediate", {
            "fields": ("intermediate_board", "intermediate_group", "intermediate_year",
                       "intermediate_marks", "intermediate_total_marks", "intermediate_grade", "intermediate_result"),
        }),
        ("Additional", {"fields": ("entry_test_score", "degree_program")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(GuardianInfo)
class GuardianInfoAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "guardian_name", "guardian_phone")
    list_filter = ("status",)
    search_fields = ("application__applicant__username", "guardian_name", "guardian_phone")
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Guardian", {
            "fields": ("guardian_name", "guardian_relationship", "guardian_cnic", "guardian_occupation",
                       "guardian_phone", "guardian_email", "guardian_address", "guardian_income"),
        }),
        ("Emergency Contact", {
            "fields": ("emergency_contact_name", "emergency_contact_relationship", "emergency_contact_number"),
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(AdditionalInfo)
class AdditionalInfoAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "hostel_required", "scholarship_required", "disability_status")
    list_filter = ("status", "hostel_required", "scholarship_required", "disability_status")
    search_fields = ("application__applicant__username",)
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Preferences", {
            "fields": ("hostel_required", "scholarship_required", "disability_status"),
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
