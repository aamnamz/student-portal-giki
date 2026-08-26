from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("help/", views.help_contact, name="help_contact"),
]
