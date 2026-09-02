from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginWithRememberMeView.as_view(template_name="accounts/login.html", authentication_form=LoginForm,), name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),    
    path("profile/", views.my_profile, name="my_profile"),
    path("change-password/", views.change_password_view, name="change_password"),
]