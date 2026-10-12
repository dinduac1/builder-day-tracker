// Builder Day Tracker — Cloudflare Worker.
// Serves the static site (env.ASSETS), stores push subscriptions (env.SUBS, KV), and every 15 minutes
// sends a Web Push notification to each device whose local time matches the start of a schedule block.
// Web Push is implemented directly on WebCrypto: VAPID (RFC 8292) + aes128gcm payload encryption (RFC 8291).

const SITE = "https://builder-day-tracker.dinduking1.workers.dev";
const VAPID_PUBLIC = "BNMbHPCzDjxThTtHX7eY2MTrtAf3vEYP08NEWrVxYOcnR_XsdNGejmcbzlyHrKBKqhJuB5pIpbeVDp1cJLuVM4k";

// Keep in step with BLOCKS in index.html
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
    const ids = new Set(BLOCKS.map(b => b.id));
    const rec = {
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
  return json({error: "Not found"}, 404);
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
      const due = BLOCKS.filter(b => b.s === hm && rec.blocks.includes(b.id));
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
