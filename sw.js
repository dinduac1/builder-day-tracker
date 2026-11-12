// ORDO service worker: keeps the app opening offline, shows reminders and crew alerts, opens ORDO when tapped.
// Pages: network first (always fresh when online), cached copy when offline.
// Files, fonts and the Firebase SDK: served from cache, refreshed in the background.
const CACHE = "ordo-v4", MEDIA_CACHE = "ordo-media";
const CORE = ["./", "ordo-anim.js", "firebase-config.js", "manifest.webmanifest", "favicon.png", "icon-192.png", "badge-72.png",
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
<main><div id="anim" style="justify-self:center"></div><h1>You're offline.</h1><p>ORDO opens as soon as you're back online.</p><button onclick="location.reload()">Try again</button></main>
<script src="ordo-anim.js"></script><script>window.ORDOAnim&&ORDOAnim.mount(document.getElementById("anim"),"charge",{size:96});addEventListener("online",()=>location.reload())</script>`, {headers: {"content-type": "text/html; charset=utf-8"}});
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
    const url = (e.notification.data && e.notification.data.url) || "./";
    for (const w of wins) if ("focus" in w) { await w.focus(); if (url.includes("open=chat")) w.postMessage({open: "chat"}); return; }
    return self.clients.openWindow(url);
  })());
});
