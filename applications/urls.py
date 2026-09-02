from django.urls import path

from . import views


urlpatterns = [
    path("continue/", views.continue_application, name="continue_application"),
    # Section I
    path("personal-information/", views.step_personal_information, name="step_personal_information"),
    path("validate-photo/", views.validate_photo_api, name="validate_photo_api"),
    path("contact-address/", views.step_contact_address, name="step_contact_address"),
    path("academic-information/", views.step_academic_information, name="step_academic_information"),
    path("program-preference/", views.step_program_preference, name="step_program_preference"),
    path("admission-test/", views.step_admission_test, name="step_admission_test"),
    path("admission-scheme/", views.step_admission_scheme, name="step_admission_scheme"),
    path("employment/", views.step_employment, name="step_employment"),
    path("application-form/", views.application_form, name="application_form"),
    path("declaration/", views.declaration, name="declaration"),
    path("review/", views.review_application, name="review_application"),
    path("submit/", views.submit_application, name="submit_application"),

    # Section II — unlocked once Section I is submitted
    path("processing-fee/", views.step_processing_fee, name="step_processing_fee"),
    path("referee-information/", views.step_referee_information, name="step_referee_information"),

    # Section III — unlocked once Section II is complete
    path("test-center/", views.step_test_center, name="step_test_center"),

    path("reset/", views.reset_application, name="reset_application"),
    path("status/", views.application_status, name="application_status"),
]