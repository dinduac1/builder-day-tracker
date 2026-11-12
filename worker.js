// Builder Day Tracker — Cloudflare Worker.
// Serves the static site (env.ASSETS), stores push subscriptions (env.SUBS, KV), and every 15 minutes
// sends a Web Push notification to each device whose local time matches the start of a schedule block.
// Web Push is implemented directly on WebCrypto: VAPID (RFC 8292) + aes128gcm payload encryption (RFC 8291).

const SITE = "https://builder-day-tracker.dinduking1.workers.dev";
const VAPID_PUBLIC = "BNMbHPCzDjxThTtHX7eY2MTrtAf3vEYP08NEWrVxYOcnR_XsdNGejmcbzlyHrKBKqhJuB5pIpbeVDp1cJLuVM4k";

// Android app (android/) signing certificate. Must match android/builderday.jks.
const CERT = ["FA:B1:C5:CA:65:A1:77:4F:35:E5:63:FF:B8:C5:2E:F3:B8:92:4A:12:C4:C7:BA:B3:38:61:9C:DF:46:12:33:B1"];
const ASSET_LINKS = ["com.ordo.app", "com.builderday.tracker"].map(package_name => ({
  relation: ["delegate_permission/common.handle_all_urls"],
  target: {namespace: "android_app", package_name, sha256_cert_fingerprints: CERT},
}));

// The default day. Devices send their own routine when they subscribe; this is the fallback.
const BLOCKS = [
  {id:"wake",    s:"05:00", e:"05:30", name:"Wake", desc:"Water, light, no phone. Read tonight's plan from last night."},
  {id:"train",   s:"05:30", e:"06:45", name:"TRAIN", desc:"Gym. Log the session."},
  {id:"study",   s:"06:45", e:"07:15", name:"Study", desc:"30 min reading in the craft."},
  {id:"build",   s:"07:15", e:"09:15", name:"BUILD — Deep Work 1", desc:"The money-making work. Phone in another room."},
  {id:"break",   s:"09:15", e:"09:45", name:"Break", desc:"Food. Walk. No feeds."},
  {id:"publish", s:"09:45", e:"11:15", name:"PUBLISH — Deep Work 2", desc:"Create + ship today's content."},
  {id:"connect", s:"11:15", e:"12:00", name:"CONNECT", desc:"10 outreach touches. Follow-ups first."},
  {id:"lunch",   s:"12:00", e:"13:00", name:"Lunch + admin", desc:"Emails, invoices, small tasks — never in deep work."},
  {id:"exec",    s:"13:00", e:"16:00", name:"Execution block", desc:"Client work, sales calls, systems, editing."},
  {id:"drills",  s:"16:00", e:"17:00", name:"Learning/skill drills", desc:"Deliberate practice on your weakest skill."},
  {id:"life",    s:"17:00", e:"20:00", name:"Life", desc:"People, food, family, faith, community."},
  {id:"review",  s:"20:30", e:"20:45", name:"REVIEW", desc:"Did I do the Five? Write tomorrow's top 3 and one line of gratitude."},
  {id:"wind",    s:"21:00", e:"22:00", name:"Wind down", desc:"No screens after 21:30."},
  {id:"sleep",   s:"22:00", e:"05:00", name:"Sleep", desc:"7+ hours, non-negotiable."},
];

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    // Lets the Android app open this site full screen (Trusted Web Activity) without a URL bar
    if (url.pathname === "/.well-known/assetlinks.json") return json(ASSET_LINKS);
    if (url.pathname.startsWith("/api/media")) {
      try { return await media(req, env, url); }
      catch (e) { return json({error: String(e && e.message || e)}, 500); }
    }
    if (url.pathname.startsWith("/api/")) {
      try { return await api(req, env, url); }
      catch (e) { return json({error: String(e && e.message || e)}, 500); }
    }
    return env.ASSETS.fetch(req);
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(tick(env, new Date(event.scheduledTime)));
  },
};

/* ---------- API ---------- */
const json = (o, status = 200) => new Response(JSON.stringify(o), {status, headers: {"content-type": "application/json"}});

async function api(req, env, url) {
  if (req.method !== "POST") return json({error: "POST only"}, 405);
  const body = await req.json().catch(() => null);
  if (!body) return json({error: "Send JSON"}, 400);

  if (url.pathname === "/api/subscribe") {
    const sub = body.subscription;
    if (!sub || typeof sub.endpoint !== "string" || !sub.endpoint.startsWith("https://") || !sub.keys || !sub.keys.p256dh || !sub.keys.auth)
      return json({error: "Invalid subscription"}, 400);
    const routine = cleanRoutine(body.routine);
    const ids = new Set((routine || BLOCKS).map(b => b.id));
    const rec = {
      routine,
      subscription: {endpoint: sub.endpoint, keys: {p256dh: sub.keys.p256dh, auth: sub.keys.auth}},
      timeZone: validTz(body.timeZone) ? body.timeZone : "Africa/Lagos",
      blocks: Array.isArray(body.blocks) ? body.blocks.filter(b => ids.has(b)) : [...ids],
      updated: Date.now(),
    };
    await env.SUBS.put(await keyOf(sub.endpoint), JSON.stringify(rec));
    return json({ok: true});
  }
  if (url.pathname === "/api/unsubscribe") {
    if (typeof body.endpoint === "string") await env.SUBS.delete(await keyOf(body.endpoint));
    return json({ok: true});
  }
  if (url.pathname === "/api/test") {
    const rec = typeof body.endpoint === "string" ? await env.SUBS.get(await keyOf(body.endpoint), "json") : null;
    if (!rec) return json({error: "This device isn't subscribed"}, 404);
    const r = await sendPush(env, rec.subscription, {title: "Reminders are on", body: "You'll get a notification as each block starts.", tag: "test"});
    return json({ok: r.ok, status: r.status});
  }
  if (url.pathname === "/api/crew/notify") return crewNotify(env, body);
  return json({error: "Not found"}, 404);
}

/* ---------- crew alerts ----------
 * A member finishing something calls this with their Firebase ID token, the crew code and the text.
 * The token is verified, the crew's devices are read from Firestore *with the caller's own token* (so the
 * database rules decide who may read them), and everyone else in the crew gets the alert:
 *   - Android app: Firebase Cloud Messaging (needs the FCM_SA_JSON secret, a Firebase service-account key)
 *   - website / home-screen app: Web Push (VAPID, already set up for reminders)
 */
const PROJECT = "builder-day-lmd5bi";
async function crewNotify(env, body) {
  const {idToken, code, title, text, tag} = body;
  if (typeof idToken !== "string" || typeof code !== "string" || !/^[A-Z0-9]{6}$/.test(code) || typeof text !== "string")
    return json({error: "Bad request"}, 400);
  const claims = await verifyFirebaseToken(idToken).catch(() => null);
  if (!claims) return json({error: "Not signed in"}, 401);
  const r = await fetch(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents/groups/${code}/devices?pageSize=200`,
    {headers: {authorization: "Bearer " + idToken}});
  if (!r.ok) return json({error: "Not a member of this crew"}, 403);
  const docs = (await r.json()).documents || [];
  const t = tag || "crew-" + code;
  const msg = {title: String(title || "Your crew").slice(0, 80), body: text.slice(0, 240), tag: t, url: t.startsWith("chat-") ? "/?open=chat" : "/"};
  let fcm = 0, web = 0;
  const fcmToken = env.FCM_SA_JSON ? await googleAccessToken(env).catch(() => null) : null;
  for (const d of docs) {
    const uid = d.name.split("/").pop();
    if (uid === claims.user_id) continue;                       // don't alert the sender
    const f = d.fields || {};
    const tokens = ((f.fcm || {}).arrayValue || {}).values || [];
    if (fcmToken) for (const t of tokens) {
      const res = await fetch(`https://fcm.googleapis.com/v1/projects/${PROJECT}/messages:send`, {method: "POST",
        headers: {authorization: "Bearer " + fcmToken, "content-type": "application/json"},
        body: JSON.stringify({message: {token: t.stringValue, data: {title: msg.title, body: msg.body, tag: msg.tag},
          android: {priority: "high"}}})});
      if (res.ok) fcm++;
    }
    const subs = ((f.web || {}).arrayValue || {}).values || [];
    for (const sv of subs) {
      try {
        const sub = JSON.parse(sv.stringValue);
        const res = await sendPush(env, sub, msg);
        if (res.ok) web++;
      } catch {}
    }
  }
  return json({ok: true, fcm, web, fcmConfigured: !!env.FCM_SA_JSON});
}

/* ---------- crew chat media ----------
 * POST /api/media?code=CREW  (Authorization: Bearer <Firebase ID token>, body = the file)
 *   only members of that crew may upload (checked by reading their member row with their own token);
 *   stored in KV under an unguessable key, returned as /api/media/CREW/<32 hex>.
 * GET  /api/media/CREW/<id>   the file, cacheable forever, with byte ranges for audio/video seeking.
 * DELETE /api/media/CREW/<id> (Bearer token) the uploader removes it.
 */
const MEDIA_MAX = 25 * 1024 * 1024;   // KV's per-value limit
const MEDIA_TYPES = /^(image\/(jpeg|png|webp|gif)|video\/(mp4|webm|quicktime|3gpp)|audio\/(webm|ogg|mp4|mpeg|aac|x-m4a|wav))$/;
const MEDIA_KEY = /^[A-Z0-9]{6}\/[0-9a-f]{32}$/;
async function media(req, env, url) {
  const bearer = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (req.method === "POST") {
    const code = url.searchParams.get("code") || "", type = (req.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
    if (!/^[A-Z0-9]{6}$/.test(code)) return json({error: "Bad crew code"}, 400);
    if (!MEDIA_TYPES.test(type)) return json({error: "That file type can't be sent here"}, 415);
    if (Number(req.headers.get("content-length") || 0) > MEDIA_MAX) return json({error: "Too big: 25 MB max"}, 413);
    const claims = await verifyFirebaseToken(bearer).catch(() => null);
    if (!claims) return json({error: "Not signed in"}, 401);
    const m = await fetch(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents/groups/${code}/members/${claims.user_id}`,
      {headers: {authorization: "Bearer " + bearer}});
    if (!m.ok) return json({error: "Not a member of this crew"}, 403);
    const body = await req.arrayBuffer();
    if (!body.byteLength) return json({error: "Empty file"}, 400);
    if (body.byteLength > MEDIA_MAX) return json({error: "Too big: 25 MB max"}, 413);
    const id = [...crypto.getRandomValues(new Uint8Array(16))].map(b => b.toString(16).padStart(2, "0")).join("");
    const key = `${code}/${id}`;
    await env.SUBS.put("m:" + key, body, {metadata: {type, uid: claims.user_id, size: body.byteLength, at: Date.now()}});
    return json({key, url: "/api/media/" + key});
  }
  const key = url.pathname.slice("/api/media/".length);
  if (!MEDIA_KEY.test(key)) return json({error: "Not found"}, 404);
  if (req.method === "DELETE") {
    const claims = await verifyFirebaseToken(bearer).catch(() => null);
    if (!claims) return json({error: "Not signed in"}, 401);
    const {metadata} = await env.SUBS.getWithMetadata("m:" + key, {type: "stream"});
    if (metadata && metadata.uid !== claims.user_id) return json({error: "Not yours"}, 403);
    await env.SUBS.delete("m:" + key);
    return json({ok: true});
  }
  if (req.method !== "GET" && req.method !== "HEAD") return json({error: "Method"}, 405);
  const {value, metadata} = await env.SUBS.getWithMetadata("m:" + key, {type: "arrayBuffer", cacheTtl: 86400});
  if (!value) return new Response("Not found", {status: 404});
  const total = value.byteLength, type = (metadata && metadata.type) || "application/octet-stream";
  const base = {"content-type": type, "cache-control": "public, max-age=31536000, immutable", "accept-ranges": "bytes", "x-content-type-options": "nosniff"};
  const range = /^bytes=(\d*)-(\d*)$/.exec(req.headers.get("range") || "");
  if (range && (range[1] || range[2])) {
    let start = range[1] ? Number(range[1]) : total - Number(range[2]), end = range[1] && range[2] ? Number(range[2]) : total - 1;
    start = Math.max(0, start); end = Math.min(total - 1, end);
    if (start > end) return new Response(null, {status: 416, headers: {"content-range": `bytes */${total}`}});
    return new Response(value.slice(start, end + 1), {status: 206, headers: {...base, "content-range": `bytes ${start}-${end}/${total}`, "content-length": String(end - start + 1)}});
  }
  return new Response(req.method === "HEAD" ? null : value, {headers: {...base, "content-length": String(total)}});
}

/** Verify a Firebase Auth ID token (RS256, Google's securetoken keys). Returns its claims. */
let jwkCache = {at: 0, keys: null};
async function verifyFirebaseToken(token) {
  const [h, p, sig] = token.split(".");
  const header = JSON.parse(new TextDecoder().decode(unb64u(h)));
  const claims = JSON.parse(new TextDecoder().decode(unb64u(p)));
  const now = Math.floor(Date.now() / 1000);
  if (claims.aud !== PROJECT || claims.iss !== "https://securetoken.google.com/" + PROJECT || claims.exp < now || !claims.user_id) throw new Error("claims");
  if (!jwkCache.keys || Date.now() - jwkCache.at > 3600_000) {
    jwkCache = {at: Date.now(), keys: (await (await fetch("https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com")).json()).keys};
  }
  const jwk = jwkCache.keys.find(k => k.kid === header.kid);
  if (!jwk) throw new Error("kid");
  const key = await crypto.subtle.importKey("jwk", jwk, {name: "RSASSA-PKCS1-v1_5", hash: "SHA-256"}, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, unb64u(sig), enc.encode(h + "." + p));
  if (!ok) throw new Error("sig");
  return claims;
}

/** OAuth access token for FCM from the service-account key in FCM_SA_JSON (cached ~50 min). */
let gTok = {at: 0, token: null};
async function googleAccessToken(env) {
  if (gTok.token && Date.now() - gTok.at < 50 * 60_000) return gTok.token;
  const sa = JSON.parse(env.FCM_SA_JSON.replace(/^﻿/, ""));
  const pem = sa.private_key.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  const der = Uint8Array.from(atob(pem), c => c.charCodeAt(0));
  const key = await crypto.subtle.importKey("pkcs8", der, {name: "RSASSA-PKCS1-v1_5", hash: "SHA-256"}, false, ["sign"]);
  const now = Math.floor(Date.now() / 1000);
  const head = b64u(enc.encode(JSON.stringify({alg: "RS256", typ: "JWT"})));
  const claim = b64u(enc.encode(JSON.stringify({iss: sa.client_email, scope: "https://www.googleapis.com/auth/firebase.messaging",
    aud: "https://oauth2.googleapis.com/token", iat: now, exp: now + 3600})));
  const sig = new Uint8Array(await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, enc.encode(head + "." + claim)));
  const r = await fetch("https://oauth2.googleapis.com/token", {method: "POST", headers: {"content-type": "application/x-www-form-urlencoded"},
    body: new URLSearchParams({grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer", assertion: `${head}.${claim}.${b64u(sig)}`})});
  const j = await r.json();
  if (!j.access_token) throw new Error("token");
  gTok = {at: Date.now(), token: j.access_token};
  return gTok.token;
}

function validTz(tz) {
  if (typeof tz !== "string" || tz.length > 64) return false;
  try { new Intl.DateTimeFormat("en-GB", {timeZone: tz}); return true; } catch { return false; }
}
async function keyOf(endpoint) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(endpoint));
  return "sub:" + b64u(new Uint8Array(h));
}

/* ---------- schedule ---------- */
function localParts(now, tz) {
  const f = new Intl.DateTimeFormat("en-GB", {timeZone: tz, hour: "2-digit", minute: "2-digit", weekday: "short", hourCycle: "h23"});
  const p = Object.fromEntries(f.formatToParts(now).map(x => [x.type, x.value]));
  return {hm: `${p.hour}:${p.minute}`, dow: p.weekday};
}
function cleanRoutine(r) {
  if (!Array.isArray(r) || !r.length) return null;
  const out = r.slice(0, 40).filter(b => b && /^[a-z0-9_]{1,24}$/i.test(b.id) && /^\d\d:\d\d$/.test(b.s))
    .map(b => ({id: b.id, s: b.s, name: String(b.name || "").slice(0, 60), desc: String(b.desc || "").slice(0, 200)}));
  return out.length ? out : null;
}
const toMin = hm => Number(hm.slice(0, 2)) * 60 + Number(hm.slice(3, 5));
function messageFor(b, dow) {
  if (b.id === "train" && dow === "Sun") return {title: "Rest day", body: "Mobility and a walk. Recover for Monday."};
  return {title: `${b.name} · ${b.s}`, body: b.desc};
}

async function tick(env, now) {
  let cursor;
  do {
    const page = await env.SUBS.list({prefix: "sub:", cursor});
    for (const k of page.keys) {
      const rec = await env.SUBS.get(k.name, "json");
      if (!rec) continue;
      const {hm, dow} = localParts(now, rec.timeZone);
      // the cron runs every 15 minutes: send every block that started since the last run
      const now = toMin(hm);
      const due = (rec.routine || BLOCKS).filter(b => rec.blocks.includes(b.id) && (now - toMin(b.s) + 1440) % 1440 < 15);
      for (const b of due) {
        const m = messageFor(b, dow);
        const r = await sendPush(env, rec.subscription, {...m, tag: "block-" + b.id});
        if (r.status === 404 || r.status === 410) { await env.SUBS.delete(k.name); break; }   // device unsubscribed
      }
    }
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
}

/* ---------- Web Push ---------- */
const enc = new TextEncoder();
function b64u(bytes) {
  let s = ""; for (const x of bytes) s += String.fromCharCode(x);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function unb64u(str) {
  const s = atob(str.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((str.length + 3) % 4));
  return Uint8Array.from(s, c => c.charCodeAt(0));
}
const concat = (...arrs) => { const out = new Uint8Array(arrs.reduce((n, a) => n + a.length, 0)); let o = 0; for (const a of arrs) { out.set(a, o); o += a.length; } return out; };

async function hkdf(salt, ikm, info, bytes) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({name: "HKDF", hash: "SHA-256", salt, info}, key, bytes * 8));
}

async function vapidHeader(env, endpoint) {
  const jwk = JSON.parse(env.VAPID_PRIVATE_JWK.replace(/^﻿/, ""));   // tolerate a byte-order mark from Windows shells
  const key = await crypto.subtle.importKey("jwk", jwk, {name: "ECDSA", namedCurve: "P-256"}, false, ["sign"]);
  const head = b64u(enc.encode(JSON.stringify({typ: "JWT", alg: "ES256"})));
  const claims = b64u(enc.encode(JSON.stringify({aud: new URL(endpoint).origin, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: SITE})));
  const sig = new Uint8Array(await crypto.subtle.sign({name: "ECDSA", hash: "SHA-256"}, key, enc.encode(`${head}.${claims}`)));
  return `vapid t=${head}.${claims}.${b64u(sig)}, k=${VAPID_PUBLIC}`;
}

// RFC 8291 aes128gcm, single record
export async function encryptPayload(sub, plaintext) {
  const uaPublic = unb64u(sub.keys.p256dh), authSecret = unb64u(sub.keys.auth);
  const local = await crypto.subtle.generateKey({name: "ECDH", namedCurve: "P-256"}, true, ["deriveBits"]);
  const asPublic = new Uint8Array(await crypto.subtle.exportKey("raw", local.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPublic, {name: "ECDH", namedCurve: "P-256"}, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({name: "ECDH", public: uaKey}, local.privateKey, 256));
  const ikm = await hkdf(authSecret, shared, concat(enc.encode("WebPush: info\0"), uaPublic, asPublic), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const aes = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const ct = new Uint8Array(await crypto.subtle.encrypt({name: "AES-GCM", iv: nonce}, aes, concat(plaintext, new Uint8Array([2]))));
  const header = new Uint8Array(21); header.set(salt, 0); new DataView(header.buffer).setUint32(16, 4096); header[20] = asPublic.length;
  return concat(header, asPublic, ct);
}

async function sendPush(env, sub, payload) {
  const body = await encryptPayload(sub, enc.encode(JSON.stringify({url: "/", ...payload})));
  return fetch(sub.endpoint, {
    method: "POST",
    headers: {
      authorization: await vapidHeader(env, sub.endpoint),
      "content-encoding": "aes128gcm",
      "content-type": "application/octet-stream",
      ttl: "900",
      urgency: "high",
    },
    body,
  });
}
