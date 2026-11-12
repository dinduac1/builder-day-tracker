"""One-off: the mic is released the moment a recording ends (and whenever the chat closes or ORDO is hidden); the chat
camera only opens the mic while recording video; videos carry a small preview frame (poster)."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

# ---- voice: let go of the mic immediately, not after saving
rep('''  r.onstop = () => {
    stream.getTracks().forEach(t => t.stop()); try { ctx && ctx.close(); } catch(e){}
    if (!send) { toast("Voice note deleted."); return; }''', '''  r.onstop = () => {
    if (!send) { toast("Voice note deleted."); return; }''')
rep('''  try { r.requestData(); } catch(e){}
  r.stop();
}
const audioBlobs = {};''', '''  try { r.requestData(); } catch(e){}
  try { r.stop(); } catch(e){}
  releaseMic(stream, ctx);   // the mic goes off now, whatever happens next
}
function releaseMic(stream, ctx){
  try { stream && stream.getTracks().forEach(t => t.stop()); } catch(e){}
  try { ctx && ctx.state !== "closed" && ctx.close(); } catch(e){}
  if (vn.stream === stream) vn.stream = null;
  if (vn.ctx === ctx) vn.ctx = null;
}
/** Nothing keeps listening or filming when you leave: chat closed, ORDO in the background, page hidden. */
function releaseAllMedia(why){
  const el = $("chatv");
  if (vn.state !== "idle") { if (el && vn.rec) stopRec(el, false); else { vn.state = "idle"; releaseMic(vn.stream, vn.ctx); } if (why) toast(why); }
  if (cc.mic) { cc.mic.getTracks().forEach(t => t.stop()); cc.mic = null; }
  if ($("ccam")) { ccClose(); if (history.state && history.state.ccam) history.back(); }
}
document.addEventListener("visibilitychange", () => { if (document.hidden) releaseAllMedia(vn.state !== "idle" ? "Recording stopped: ORDO went to the background." : ""); });
const audioBlobs = {};''')
rep('''  if (!$("chatv")) { vn.stream.getTracks().forEach(t => t.stop()); vn.state = "idle"; return false; }''',
    '''  if (!$("chatv") || document.hidden) { releaseMic(vn.stream, null); vn.state = "idle"; return false; }''')
rep('''function closeChatBack(){
  if (history.state && history.state.chat) return;   // a screen opened over the chat closed; the chat stays
  chat.open = false;''', '''function closeChatBack(){
  if (history.state && history.state.chat) return;   // a screen opened over the chat closed; the chat stays
  releaseAllMedia();
  chat.open = false;''')

# ---- chat camera: video only until you hold to record
rep('''  try { cc.stream = await navigator.mediaDevices.getUserMedia({video: v, audio: true}); }
  catch(e) { try { cc.stream = await navigator.mediaDevices.getUserMedia({video: v}); } catch(e2) { cc.stream = null; } }''',
    '''  try { cc.stream = await navigator.mediaDevices.getUserMedia({video: v}); } catch(e) { cc.stream = null; }   // no mic until you record''')
rep('''function ccRecord(el, c){
  if (!cc.stream || cc.rec) return;
  const mime''', '''async function ccRecord(el, c){
  if (!cc.stream || cc.rec || cc.starting) return;
  cc.starting = true; cc.stopReq = false;
  let mic = null; try { mic = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true}}); } catch(e) { mic = null; }
  cc.starting = false;
  if (!$("ccam") || !cc.stream) { if (mic) mic.getTracks().forEach(t => t.stop()); return; }
  cc.mic = mic;
  const rs = new MediaStream([...cc.stream.getVideoTracks(), ...(mic ? mic.getAudioTracks() : [])]);
  const mime''')
rep('''  try { cc.rec = new MediaRecorder(cc.stream, mime ?''', '''  try { cc.rec = new MediaRecorder(rs, mime ?''')
rep('''  catch(e) { toast("This phone can't record video here."); return; }
  cc.chunks = []; cc.t0 = Date.now();''', '''  catch(e) { if (mic) mic.getTracks().forEach(t => t.stop()); cc.mic = null; toast("This phone can't record video here."); return; }
  cc.chunks = []; cc.t0 = Date.now();''')
rep('''  tick();
  try { navigator.vibrate && navigator.vibrate(30); } catch(e){}
}
function ccStopRecord(el, c){
  const r = cc.rec; if (!r) return;
  cc.rec = null; cancelAnimationFrame(cc.raf);''', '''  tick();
  try { navigator.vibrate && navigator.vibrate(30); } catch(e){}
  if (cc.stopReq) ccStopRecord(el, c);   // let go while the mic was starting
}
function ccStopRecord(el, c){
  const r = cc.rec; if (!r) { if (cc.starting) cc.stopReq = true; return; }
  cc.rec = null; cancelAnimationFrame(cc.raf);''')
rep('''  try { r.requestData(); } catch(e){}
  r.stop();
}

function viewImage(el, src){''', '''  try { r.requestData(); } catch(e){}
  r.stop();
  if (cc.mic) { cc.mic.getTracks().forEach(t => t.stop()); cc.mic = null; }   // mic off as soon as you let go
}

function viewImage(el, src){''')
rep('''  if (cc.stream) cc.stream.getTracks().forEach(t => t.stop()); cc.stream = null; cancelAnimationFrame(cc.raf);''',
    '''  if (cc.stream) cc.stream.getTracks().forEach(t => t.stop()); cc.stream = null; cancelAnimationFrame(cc.raf);
  if (cc.mic) { cc.mic.getTracks().forEach(t => t.stop()); cc.mic = null; }''')

# ---- video previews (poster frames)
rep('''const mb = n => (n / 1048576).toFixed(n < 10485760 ? 1 : 0) + " MB";''', '''const mb = n => (n / 1048576).toFixed(n < 10485760 ? 1 : 0) + " MB";
const BLANK_POSTER = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
/** A small preview frame (≈480 px JPEG) of a video at time t, so the chat shows the video instead of a placeholder. */
async function makePoster(url, t){
  const v = document.createElement("video"); v.muted = true; v.preload = "auto"; v.playsInline = true; v.src = url;
  try {
    await new Promise((r, j) => { v.onloadeddata = r; v.onerror = j; setTimeout(r, 4000); });
    if (!isFinite(v.duration)) await realDuration(v);
    v.currentTime = Math.max(.05, t || 0); await new Promise(r => { v.onseeked = r; setTimeout(r, 2500); });
    const k = Math.min(1, 480 / Math.max(v.videoWidth || 480, v.videoHeight || 480)), c = document.createElement("canvas");
    c.width = Math.round((v.videoWidth || 480) * k); c.height = Math.round((v.videoHeight || 480) * k);
    c.getContext("2d").drawImage(v, 0, 0, c.width, c.height);
    return {poster: c.toDataURL("image/jpeg", .68), w: v.videoWidth, h: v.videoHeight};
  } catch(e) { return {}; } finally { v.removeAttribute("src"); v.load(); }
}''')
rep('''          ready.push([out, "video", {w: it.w || 0, h: it.h || 0, dur: Math.round((it.end - it.start) * 10) / 10}]);''',
    '''          const pv = await makePoster(it.url, it.start);
          ready.push([out, "video", {w: it.w || pv.w || 0, h: it.h || pv.h || 0, dur: Math.round((it.end - it.start) * 10) / 10, ...(pv.poster ? {poster: pv.poster} : {})}]);''')
rep('''          ready.push([it.file, "video", {w: 0, h: 0, dur: it.dur || 0}]);''',
    '''          const pv = await makePoster(it.url, 0);
          ready.push([it.file, "video", {w: pv.w || 0, h: pv.h || 0, dur: it.dur || 0, ...(pv.poster ? {poster: pv.poster} : {})}]);''')
rep('''          const v = document.createElement("video"); v.src = src; v.controls = true; v.playsInline = true; v.preload = "metadata";''',
    '''          const v = document.createElement("video"); v.controls = true; v.playsInline = true; v.preload = "metadata";
          v.poster = it.media.poster || BLANK_POSTER;                                  // never Android's grey placeholder
          v.src = it.media.poster || it.pending ? src : src + "#t=0.1";               // older videos: show their first frame''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
