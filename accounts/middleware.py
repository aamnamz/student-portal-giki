from django.shortcuts import redirect
from django.urls import reverse
from accounts.models import Profile


class ProgramSelectionMiddleware:
    """
    Middleware that enforces mandatory graduate program selection (MS/PhD)
    for logged-in users who do not have a program saved on their profile.

    This funnels Google sign-up users (or any user missing a profile.program)
    to the mandatory program selection landing page on every login or protected route visit
    until they make a selection.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info

            try:
                select_program_url = reverse("accounts:select_program")
            except Exception:
                select_program_url = "/accounts/select-program/"

            try:
                logout_url = reverse("accounts:logout")
            except Exception:
                logout_url = "/accounts/logout/"

            if (
                path.startswith(select_program_url)
                or path.startswith(logout_url)
                or path.startswith("/admin/")
                or path.startswith("/static/")
                or path.startswith("/media/")
            ):
                return self.get_response(request)

            profile, _ = Profile.objects.get_or_create(user=request.user)
            if not profile.program:
                return redirect(select_program_url)

        return self.get_response(request)
