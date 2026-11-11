"""One-off: crew chat media (photos, videos, voice notes) stored in Workers KV, members-only upload, unguessable links."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker.js")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
rep('''    if (url.pathname.startsWith("/api/")) {
      try { return await api(req, env, url); }''', '''    if (url.pathname.startsWith("/api/media")) {
      try { return await media(req, env, url); }
      catch (e) { return json({error: String(e && e.message || e)}, 500); }
    }
    if (url.pathname.startsWith("/api/")) {
      try { return await api(req, env, url); }''')
rep('''/** Verify a Firebase Auth ID token''', '''/* ---------- crew chat media ----------
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

/** Verify a Firebase Auth ID token''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
