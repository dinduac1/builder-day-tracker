// Service worker: shows schedule reminders pushed by the Worker and opens the tracker when tapped.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = {body: e.data && e.data.text()}; }
  e.waitUntil(self.registration.showNotification(d.title || "Builder Day", {
    body: d.body || "",
    tag: d.tag || "builder-day",
    renotify: true,
    icon: "icon-192.png",
    badge: "badge-72.png",
    data: {url: d.url || "./"},
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil((async () => {
    const wins = await self.clients.matchAll({type: "window", includeUncontrolled: true});
    for (const w of wins) if ("focus" in w) return w.focus();
    return self.clients.openWindow(e.notification.data && e.notification.data.url || "./");
  })());
});
