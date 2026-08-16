from django.urls import path

from . import views

urlpatterns = [
    path("", views.my_application, name="my_application"),
    path("personal-information/", views.step_personal_information, name="step_personal_information"),
    path("validate-photo/", views.validate_photo_api, name="validate_photo_api"),
    path("contact-address/", views.step_contact_address, name="step_contact_address"),
    path("academic-information/", views.step_academic_information, name="step_academic_information"),
    path("guardian-information/", views.step_guardian_information, name="step_guardian_information"),
    path("additional-information/", views.step_additional_information, name="step_additional_information"),
    path("declaration/", views.declaration, name="declaration"),
    path("review/", views.review_application, name="review_application"),
    path("submit/", views.submit_application, name="submit_application"),
    path("reset/", views.reset_application, name="reset_application"),
    path("status/", views.application_status, name="application_status"),
]
