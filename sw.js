// ORDO service worker: keeps the app opening offline, shows reminders and crew alerts, opens ORDO when tapped.
// Pages: network first (always fresh when online), cached copy when offline.
// Files, fonts and the Firebase SDK: served from cache, refreshed in the background.
const CACHE = "ordo-v3", MEDIA_CACHE = "ordo-media";
const CORE = ["./", "firebase-config.js", "manifest.webmanifest", "favicon.png", "icon-192.png", "badge-72.png",
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js",
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js",
  "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"];
const SHELL_HOSTS = ["www.gstatic.com", "fonts.googleapis.com", "fonts.gstatic.com"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k !== CACHE && k !== MEDIA_CACHE) await caches.delete(k);
  await self.clients.claim();
})()));

self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET") return;
  const same = url.origin === self.location.origin;
  if (same && url.pathname.startsWith("/api/media/")) {               // chat photos, videos, voice notes: download once
    e.respondWith((async () => {
      const c = await caches.open(MEDIA_CACHE), hit = await c.match(url.pathname);
      if (hit) return hit;
      if (req.headers.has("range")) { e.waitUntil(fetch(url.pathname).then(r => r.ok && c.put(url.pathname, r)).catch(() => {})); return fetch(req); }
      const res = await fetch(req); if (res.ok) c.put(url.pathname, res.clone()); return res;
    })());
    return;
  }
  if (same && url.pathname.startsWith("/api/")) return;              // reminder / crew server: always live
  if (!same && !SHELL_HOSTS.includes(url.hostname)) return;          // Firebase, YouTube etc. handle themselves
  if (req.mode === "navigate") {
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res.ok) { const c = await caches.open(CACHE); c.put("./", res.clone()); }
        return res;
      } catch (err) {
        return (await caches.match("./")) || offlinePage();
      }
    })());
    return;
  }
  e.respondWith((async () => {
    const c = await caches.open(CACHE), hit = await c.match(req);
    const fresh = fetch(req).then(res => { if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone()); return res; }).catch(() => null);
    if (hit) { e.waitUntil(fresh); return hit; }
    return (await fresh) || new Response("", {status: 504});
  })());
});

function offlinePage() {
  return new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ORDO · Offline</title>
<style>html,body{margin:0;height:100%;background:#08090C;color:#F3F1EC;font-family:system-ui,sans-serif}main{min-height:100%;display:grid;place-content:center;gap:14px;text-align:center;padding:24px}
h1{margin:6px 0 0;font-size:30px;letter-spacing:.04em}p{margin:0;color:rgba(243,241,236,.6);max-width:300px}.ordo-load{width:88px;height:88px;display:block;border-radius:21px;box-shadow:0 18px 50px rgba(0,0,0,.45)}.ordo-load .ol-rot{transform-origin:32px 32px;animation:ol-rot 1.5s linear infinite}.ordo-load .ol-iv{stroke-dasharray:54 110;stroke-dashoffset:-20;animation:ol-iv 1.5s ease-in-out infinite}@keyframes ol-rot{to{transform:rotate(-360deg)}}@keyframes ol-iv{0%,100%{stroke-dasharray:34 110}50%{stroke-dasharray:74 110}}.ol-word{font-family:'Big Shoulders Display',system-ui,sans-serif;font-weight:800;letter-spacing:.36em;font-size:15px;color:rgba(243,241,236,.62);margin-left:.36em}.ol-dots::after{content:'';animation:ol-dots 1.5s steps(4) infinite}@keyframes ol-dots{0%{content:''}25%{content:'.'}50%{content:'..'}75%{content:'...'}}@media (prefers-reduced-motion:reduce){.ordo-load .ol-rot{animation-duration:4s}.ordo-load .ol-iv{animation:none}}.s{font-family:monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#7C8BFF}button{justify-self:center;margin-top:10px;border:0;border-radius:999px;background:#F3F1EC;color:#08090C;font-weight:700;font-size:15px;padding:13px 26px}</style>
<main><svg class="ordo-load" style="justify-self:center" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="15" fill="#111318"/><circle cx="32" cy="32" r="17.5" fill="none" stroke="rgba(243,241,236,.08)" stroke-width="6.6"/><g class="ol-rot"><g transform="rotate(-90 32 32)"><circle class="ol-iv" cx="32" cy="32" r="17.5" fill="none" stroke="#F3F1EC" stroke-width="6.6" stroke-linecap="round"/><circle cx="32" cy="32" r="17.5" fill="none" stroke="#7C8BFF" stroke-width="6.6" stroke-linecap="round" stroke-dasharray="11 110"/></g></g></svg><h1>You're offline.</h1><p>ORDO opens as soon as you're back online.</p><div class="s">Reconnecting<span class="ol-dots"></span></div><button onclick="location.reload()">Try again</button></main>
<script>addEventListener("online",()=>location.reload())</script>`, {headers: {"content-type": "text/html; charset=utf-8"}});
}

self.addEventListener("push", e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch { d = {body: e.data && e.data.text()}; }
  e.waitUntil(self.registration.showNotification(d.title || "ORDO", {
    body: d.body || "",
    tag: d.tag || "ordo",
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
