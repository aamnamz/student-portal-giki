from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from allauth.socialaccount.providers.google.views import oauth2_callback as google_oauth2_callback

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("application/", include("applications.urls")),
    path("documents/", include("documents.urls")),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("auth/callback/google", google_oauth2_callback, name="google_callback"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
