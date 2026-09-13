importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyCY7AHDQqRh7BFwg6P1jPzstd8K7Cf0M8Q",
  authDomain: "graduate-admission-portal.firebaseapp.com",
  projectId: "graduate-admission-portal",
  storageBucket: "graduate-admission-portal.firebasestorage.app",
  messagingSenderId: "4275246204",
  appId: "1:4275246204:web:76ee5dc48a2814345365f9",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "GIKI Applicant Portal";
  const options = {
    body: payload.notification?.body || "",
    icon: "/static/dashboard/images/giki.png",
    data: payload.data || {},
  };
  self.registration.showNotification(title, options);
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const link = event.notification.data?.link;
  if (link) {
    event.waitUntil(clients.openWindow(link));
  }
});