function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return null;
  return navigator.serviceWorker.register("/firebase-messaging-sw.js");
}

async function registerFCMTokenOnServer(token, deviceType = "web") {
  const response = await fetch("/api/fcm/register/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ token, device_type: deviceType }),
  });
  return response.ok;
}

async function unregisterFCMTokenOnServer(token) {
  const response = await fetch("/api/fcm/unregister/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ token }),
  });
  return response.ok;
}

/**
 * Obtains an FCM registration token and syncs it with the backend.
 * Does NOT prompt for permission — call this only after permission is
 * already granted (e.g. from a future settings toggle).
 */
async function initFCM() {
  if (Notification.permission !== "granted") return null;

  const registration = await registerServiceWorker();
  if (!registration) return null;

  const messaging = firebase.messaging();
  const token = await messaging.getToken({
    vapidKey: window.FCM_VAPID_KEY,
    serviceWorkerRegistration: registration,
  });

  if (token) {
    await registerFCMTokenOnServer(token);
  }
  return token;
}

window.giki_fcm = { registerServiceWorker, initFCM, registerFCMTokenOnServer, unregisterFCMTokenOnServer };