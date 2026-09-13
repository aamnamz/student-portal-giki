import logging

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import NotFoundError
from .models import FCMDeviceToken, notify   
from .models import FCMDeviceToken

logger = logging.getLogger(__name__)

_app = None


def initialize_firebase_admin():
    """Initialize the Firebase Admin app once, reusing it on subsequent calls."""
    global _app
    if _app is not None:
        return _app

    try:
        if settings.FIREBASE_CREDENTIALS_PATH:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            _app = firebase_admin.initialize_app(cred)
        else:
            _app = firebase_admin.initialize_app()
    except ValueError:
        # App already initialized elsewhere (e.g. autoreload double-import)
        _app = firebase_admin.get_app()

    return _app


def send_fcm_notification(user, title, body, data=None, link=None, level="info", persist=True):
    """
    Send a push notification to every registered device for `user`, and
    (by default) also create an in-app Notification row so it shows in
    the bell icon regardless of whether the push itself is delivered.
    """
    if persist:
        notify(user, title=title, message=body, level=level, link=link or "")

    tokens = list(FCMDeviceToken.objects.filter(user=user).values_list("token", flat=True))
    if not tokens:
        return {"sent": 0, "failed": 0}

    initialize_firebase_admin()

    message_data = dict(data or {})
    if link:
        message_data["link"] = link

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in message_data.items()},
        tokens=tokens,
    )

    try:
        response = messaging.send_each_for_multicast(message)
    except Exception:
        logger.exception("FCM send failed for user_id=%s", user.pk)
        return {"sent": 0, "failed": len(tokens)}

    invalid_tokens = []
    for token, result in zip(tokens, response.responses):
        if result.success:
            continue
        error = result.exception
        if isinstance(error, NotFoundError) or "UNREGISTERED" in str(error).upper():
            invalid_tokens.append(token)
        else:
            logger.warning("FCM send failed for token=%s: %s", token, error)

    if invalid_tokens:
        FCMDeviceToken.objects.filter(token__in=invalid_tokens).delete()

    return {"sent": response.success_count, "failed": response.failure_count}