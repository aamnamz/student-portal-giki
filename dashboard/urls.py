from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # My Application (5-step form)
    path("application/", views.my_application, name="my_application"),
    path("application/personal-information/", views.step_personal_information, name="step_personal_information"),
    path("application/contact-address/", views.step_contact_address, name="step_contact_address"),
    path("application/academic-information/", views.step_academic_information, name="step_academic_information"),
    path("application/guardian-information/", views.step_guardian_information, name="step_guardian_information"),
    path("application/review/", views.review_application, name="review_application"),
    path("application/submit/", views.submit_application, name="submit_application"),

    # Documents
    path("documents/", views.documents, name="documents"),

    # Profile
    path("profile/", views.my_profile, name="my_profile"),

    # Application status timeline
    path("status/", views.application_status, name="application_status"),

    # Settings
    path("settings/", views.settings_view, name="settings"),

    # Help / Contact Admissions
    path("help/", views.help_contact, name="help_contact"),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
]