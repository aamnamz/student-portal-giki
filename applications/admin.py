from django.contrib import admin
from django.utils.html import format_html

from .models import Application, PersonalInfo, ContactAddress, AcademicInfo


class PersonalInfoInline(admin.TabularInline):
    model = PersonalInfo
    extra = 0
    max_num = 1
    fields = ("status", "full_name", "father_name", "cnic", "gender")


class ContactAddressInline(admin.TabularInline):
    model = ContactAddress
    extra = 0
    max_num = 1
    fields = ("status", "permanent_phone", "permanent_city", "permanent_district")


class AcademicInfoInline(admin.TabularInline):
    model = AcademicInfo
    extra = 0
    max_num = 1
    fields = ("status", "degree_certificate", "board_university", "passing_year")



@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "status", "progress_percent", "sections_completed_count", "updated_at")
    list_filter = ("status",)
    search_fields = ("applicant__username", "applicant__first_name", "applicant__last_name")
    readonly_fields = ("progress_percent", "sections_completed_count", "created_at", "updated_at")
    inlines = [PersonalInfoInline, ContactAddressInline, AcademicInfoInline]
    fieldsets = (
        ("Status", {"fields": ("applicant", "status", "declaration_accepted")}),
        ("Progress", {"fields": ("progress_percent", "sections_completed_count")}),
        ("Timestamps", {"fields": ("submitted_at", "created_at", "updated_at")}),
    )


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "full_name", "cnic", "nationality")
    list_filter = ("status", "gender", "nationality", "religion", "domicile_province")
    search_fields = (
        "application__applicant__username",
        "full_name",
        "father_name",
        "cnic",
        "passport_no",
    )
    readonly_fields = ("student_photo_preview",)
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Photo", {"fields": ("student_photo_preview", "student_photo_type")}),
        ("Personal Details", {
            "fields": (
                "full_name",
                "father_name",
                "guardian_name",
                "guardian_contact_no",
                "cell_no",
                "date_of_birth",
                "gender",
                "religion",
                "nationality",
            ),
        }),
        ("Identification", {"fields": ("cnic", "passport_no")}),
        ("Domicile", {"fields": ("domicile_province", "domicile_district")}),
        ("Additional", {"fields": ("disability_status",)}),
    )

    def student_photo_preview(self, obj):
        if not obj.student_photo:
            return "—"
        return format_html(
            '<img src="data:{};base64,{}" style="max-height:150px;" />',
            obj.student_photo_type or "image/jpeg",
            obj.student_photo,
        )

    student_photo_preview.short_description = "Photo Preview"


@admin.register(ContactAddress)
class ContactAddressAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "permanent_city", "permanent_phone", "mailing_same_as_permanent")
    list_filter = ("status", "permanent_district")
    search_fields = (
        "application__applicant__username",
        "permanent_city",
        "permanent_phone",
        "mailing_phone",
    )
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Permanent Address", {
            "fields": (
                "permanent_house_street_no",
                "permanent_mohalla_tehsil",
                "permanent_district",
                "permanent_city",
                "permanent_phone",
                "permanent_courier_available",
            ),
        }),
        ("Mailing Address", {
            "fields": (
                "mailing_same_as_permanent",
                "mailing_house_street_no",
                "mailing_mohalla_tehsil",
                "mailing_district",
                "mailing_city",
                "mailing_phone",
                "mailing_courier_available",
            ),
        }),
    )


@admin.register(AcademicInfo)
class AcademicInfoAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "degree_certificate", "board_university", "passing_year", "result_declared")
    list_filter = ("status", "degree_certificate", "study_group", "result_declared")
    search_fields = (
        "application__applicant__username",
        "board_university",
        "institute_name",
        "degree_title",
    )
    fieldsets = (
        ("Status", {"fields": ("application", "status")}),
        ("Qualification", {
            "fields": (
                "degree_certificate",
                "board_university",
                "degree_title",
                "institute_name",
                "study_group",
                "country_studied",
            ),
        }),
        ("Result", {"fields": ("obtained_marks", "total_marks", "passing_year", "result_declared")}),
    )
