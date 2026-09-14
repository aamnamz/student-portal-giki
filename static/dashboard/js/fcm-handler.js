function getCookie(name) {
  if (window.getCsrfCookie) return window.getCsrfCookie(name);
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

/**
 * Foreground push listener — fires when a push arrives while the tab is
 * open and focused (onBackgroundMessage in the service worker handles the
 * closed/backgrounded case separately). Repaints the bell live instead of
 * waiting for the next page load.
 */
function listenForForegroundMessages() {
  if (typeof firebase === "undefined" || !firebase.messaging) return;
  const messaging = firebase.messaging();

  messaging.onMessage(function (payload) {
    console.log("🔥 FCM MESSAGE RECEIVED:", payload);
  refreshNotificationBell().then(function () {
    console.log("✅ NOTIFICATION BELL REFRESHED");
    openNotificationDropdown();
  });
  refreshDashboardSummary();
  playNotificationSound();
});
}

/**
 * Plays a short two-tone chime on a live push, using the Web Audio API
 * so no external sound file needs to be hosted/loaded. Browsers only
 * allow audio after a user gesture on the page (click/keypress/etc) —
 * if none has happened yet, playback silently no-ops instead of throwing,
 * which is expected behavior on a freshly loaded, untouched tab.
 */
function playNotificationSound() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();

    const playTone = function (freq, startTime, duration) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, startTime);
      gain.gain.exponentialRampToValueAtTime(0.2, startTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(startTime);
      osc.stop(startTime + duration);
    };

    const now = ctx.currentTime;
    playTone(880, now, 0.15);
    playTone(1175, now + 0.12, 0.18);
  } catch (e) {
    console.warn("Notification sound failed:", e);
  }
}

/**
 * Opens the notification dropdown (used to auto-reveal newly arrived
 * notifications on a live FCM push). Mirrors the same .open class /
 * aria-expanded state dashboard.js's manual trigger click toggles.
 */
function openNotificationDropdown() {
  const trigger = document.getElementById("notificationTrigger");
  const dropdown = document.getElementById("notificationDropdown");
  if (!trigger || !dropdown) return;
  dropdown.classList.add("open");
  trigger.setAttribute("aria-expanded", "true");
}

async function refreshNotificationBell() {
  const response = await fetch("/api/notifications/feed/", { cache: "no-store" });
  if (!response.ok) return;
  const data = await response.json();
  renderNotificationBell(data);
}

function renderNotificationBell(data) {
  const badge = document.querySelector(".badge-dot");
  if (data.count > 0) {
    if (badge) {
      badge.textContent = data.count;
    } else {
      const trigger = document.getElementById("notificationTrigger");
      if (trigger) {
        const span = document.createElement("span");
        span.className = "badge-dot";
        span.textContent = data.count;
        trigger.appendChild(span);
      }
    }
  } else if (badge) {
    badge.remove();
  }

  const dropdown = document.getElementById("notificationDropdown");
  if (!dropdown) return;

  if (data.items.length === 0) {
    dropdown.innerHTML = '<div class="notification-empty">No new notifications</div>';
    return;
  }

  const existingClearUrl = document.getElementById("clearAllNotifications")?.dataset.clearUrl || "/notifications/clear/";

  const header =
    '<div class="notification-header d-flex justify-content-between align-items-center">' +
      '<span class="notification-header-title">Notifications</span>' +
      '<button class="notification-clear-all" type="button" id="clearAllNotifications" data-clear-url="' + existingClearUrl + '">' +
        "Clear all" +
      "</button>" +
    "</div>";

  const rows = data.items.map(function (n) {
    const content = n.link
      ? '<a class="notification-content" href="' + n.link + '"><strong>' + n.title + "</strong>" + (n.message ? "<span>" + n.message + "</span>" : "") + "</a>"
      : '<div class="notification-content"><strong>' + n.title + "</strong>" + (n.message ? "<span>" + n.message + "</span>" : "") + "</div>";

    const readBtn = n.is_read
      ? ""
      : '<button class="notification-read" type="button" data-read-url="' + n.read_url + '" aria-label="Mark ' + n.title + ' as read">Mark read</button>';

    return '<div class="notification-row ' + (n.is_read ? "" : "unread") + ' notification-' + n.level + '">' + content + readBtn + "</div>";
  }).join("");

  dropdown.innerHTML = header + rows;
}

/**
 * Refreshes the dashboard's own data fields (deadline, status, important
 * dates) the same way refreshNotificationBell() refreshes the bell.
 * Called from onMessage so a push doesn't just add a notification but also
 * patches any dashboard fields that notification was about.
 */
async function refreshDashboardSummary() {
  const response = await fetch("/api/dashboard/summary/", { cache: "no-store" });
  if (!response.ok) return;
  const data = await response.json();
  renderDashboardSummary(data);
}

function renderDashboardSummary(data) {
  const deadlineEl = document.getElementById("applicationDeadlineValue");
  if (deadlineEl) deadlineEl.textContent = data.application_deadline;

  const statusBadge = document.getElementById("applicationStatusBadge");
  if (statusBadge) {
    statusBadge.textContent = data.status_label;
    statusBadge.className = "status-badge status--" + data.status_key;
  }

  const datesList = document.getElementById("importantDatesList");
  if (datesList && Array.isArray(data.important_dates)) {
    datesList.innerHTML = data.important_dates.map(function (d) {
      return (
        '<div class="date-row ' + (d.urgent ? "date-row--urgent" : "") + '">' +
          '<div class="date-icon">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 3v3M16 3v3"/></svg>' +
          "</div>" +
          "<div>" +
            '<div class="date-label">' + d.label + "</div>" +
            '<div class="date-value">' + d.value + "</div>" +
          "</div>" +
        "</div>"
      );
    }).join("");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  listenForForegroundMessages();
  initFCM();
});

window.giki_fcm = {
  registerServiceWorker,
  initFCM,
  registerFCMTokenOnServer,
  unregisterFCMTokenOnServer,
  refreshNotificationBell,
  refreshDashboardSummary,
  playNotificationSound,
  listenForForegroundMessages,
};