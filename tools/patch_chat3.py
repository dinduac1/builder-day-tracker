"""One-off: chat done properly. Voice notes: tap = locked recording with Send/trash, hold = release to send, slide up to
lock, slide left to cancel, permission prompts can't strand a recording; playback downloads once then plays locally.
ORDO camera in chat: instant, tap shutter = photo, hold = video (ring fills), flip, flash, gallery. @ lists the whole crew."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
def cut(a, b, new):
    global s
    i = s.index(a); j = s.index(b, i)
    s = s[:i] + new + s[j:]

# ---- mentions: everyone in the crew (handle if they have one, else their name)
rep('''const mentionsMe = t => !!myHandle() && new RegExp(`@${myHandle()}\\\\b`, "i").test(t || "");''',
    '''const mentionTag = m => (m.handle || firstName(m.name).toLowerCase().replace(/[^a-z0-9_]/g, "")) || "";
const myTags = () => [myHandle(), firstName(profile().name || "").toLowerCase().replace(/[^a-z0-9_]/g, "")].filter(x => x && x.length >= 2);
const mentionsMe = t => myTags().some(h => new RegExp(`@${h}\\\\b`, "i").test(t || ""));''')
rep('''  const handles = new Set(crewState.members.map(m => (m.handle || "").toLowerCase()).filter(Boolean)); if (myHandle()) handles.add(myHandle());
  const re = /(@[a-z0-9_]{3,20})|(https?:\\/\\/[^\\s<]+)/gi; let last = 0, m;''', '''  const handles = new Set(crewState.members.map(m => mentionTag(m).toLowerCase()).filter(Boolean)); myTags().forEach(h => handles.add(h));
  const mine = new Set(myTags());
  const re = /(@[a-z0-9_]{2,20})|(https?:\\/\\/[^\\s<]+)/gi; let last = 0, m;''')
rep('''s.className = "mention" + (m[1].slice(1).toLowerCase() === myHandle() ? " mine" : "");''', '''s.className = "mention" + (mine.has(m[1].slice(1).toLowerCase()) ? " mine" : "");''')
cut("  // @mention suggestions\n", "  ta.onclick = mentionPick;", r'''  // @mention suggestions: the whole crew, as soon as you type @
  function mentionPick(){
    const pre = ta.value.slice(0, ta.selectionStart), m = /(^|\s)@([a-z0-9_]*)$/i.exec(pre);
    if (!m) { men.hidden = true; return; }
    const q = m[2].toLowerCase(), me = (crewFS() || {}).uid;
    const others = crewState.members.filter(x => x.uid !== me);
    const list = others.filter(x => !q || mentionTag(x).toLowerCase().startsWith(q) || (x.name || "").toLowerCase().startsWith(q)).slice(0, 8);
    men.hidden = false; men.innerHTML = "";
    if (!list.length) { men.innerHTML = `<div class="mnone">${others.length ? "No one in your crew matches @" + esc(q) : "You're the only one in this crew so far. Invite your people from the Crew panel."}</div>`; return; }
    list.forEach(x => { const tag = mentionTag(x); const b = document.createElement("button"); b.innerHTML = `<span class="av">${avatarHtml(x.uid, x.name)}</span><span><b></b><small></small></span>`;
      b.querySelector("b").textContent = x.name || ""; b.querySelector("small").textContent = "@" + tag;
      b.onmousedown = e => e.preventDefault();
      b.onclick = () => { const start = pre.length - m[2].length - 1; ta.value = ta.value.slice(0, start) + "@" + tag + " " + ta.value.slice(ta.selectionStart); ta.focus(); const c = start + tag.length + 2; ta.setSelectionRange(c, c); men.hidden = true; mode(); };
      men.appendChild(b); });
  }
''')
rep('''  ta.onclick = mentionPick;''', '''  ta.onclick = mentionPick; ta.onkeyup = mentionPick;''')

# ---- composer: recording bar markup
rep('''      <div class="rec" hidden><span class="dotr"></span><span class="rt">0:00</span><span class="hint">‹ Slide to cancel</span></div></div>`;''',
    '''      <div class="rec" hidden><button class="rtrash" aria-label="Delete recording">${CI.del}</button><span class="dotr"></span><span class="rt">0:00</span><canvas class="rwave" width="300" height="40"></canvas><span class="hint">‹ Slide to cancel</span></div>
      <div class="rlock" hidden><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="6" y="11" width="12" height="9" rx="2"/><path d="M9 11V8a3 3 0 0 1 6 0v3"/></svg><span>▲</span></div></div>`;''')

# ---- composer wiring: tap / hold / slide
cut("  // send, or hold to record\n", "  el.querySelector(\".att\").onclick = () => pickGallery(el);", r'''  // voice notes: tap = locked recording (Send / trash), hold = release to send, slide up = lock, slide left = cancel
  let sx = 0, sy = 0, downAt = 0, pressing = false;
  snd.onpointerdown = e => {
    if (snd.dataset.mode === "send" || vn.state === "lock" || vn.state === "starting") return;
    e.preventDefault(); sx = e.clientX; sy = e.clientY; downAt = Date.now(); pressing = true;
    try { snd.setPointerCapture(e.pointerId); } catch(_) {}
    startRec(el).then(ok => { if (ok && (!pressing || Date.now() - downAt < 350 && !pressing)) setLock(el); });
  };
  snd.onpointermove = e => {
    if (!pressing || vn.state !== "hold") return;
    if (e.clientX - sx < -90) { pressing = false; stopRec(el, false); }
    else if (sy - e.clientY > 70) { pressing = false; setLock(el); }
  };
  snd.onpointerup = () => {
    if (!pressing) return; pressing = false;
    if (vn.state === "hold") { if (Date.now() - downAt < 350) setLock(el); else stopRec(el, true); }
  };
  snd.onpointercancel = () => { if (pressing && vn.state === "hold") setLock(el); pressing = false; };   // interrupted (a prompt, a call): keep it
  snd.onclick = () => {
    if (vn.state === "lock") { if (Date.now() - vn.lockAt > 400) stopRec(el, true); return; }
    if (snd.dataset.mode === "send") send();
  };
  el.querySelector(".rtrash").onclick = () => stopRec(el, false);
  el.querySelector(".att").onclick = () => pickGallery(el);
  cam2.onclick = () => chatCamera(el);
''')
rep('''  el.querySelector(".att").onclick = () => pickGallery(el);
  cam2.onclick = () => chatCamera(el);
  el.querySelector(".att").onclick = () => pickGallery(el);
  cam2.onclick = () => cameraSheet(el);''', '''  el.querySelector(".att").onclick = () => pickGallery(el);
  cam2.onclick = () => chatCamera(el);''')

# ---- voice notes engine + playback
cut("// ---- voice notes\n", "function viewImage(", r'''// ---- voice notes
const vn = {state: "idle", rec: null, stream: null, chunks: [], t0: 0, levels: [], timer: null, sample: null, ctx: null, audio: null, playing: null, lockAt: 0};
const REC_MIME = () => ["audio/webm;codecs=opus", "audio/mp4", "audio/ogg;codecs=opus", "audio/webm"].find(t => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
/** Start recording. Resolves true once it's actually recording (after any permission prompt). */
async function startRec(el){
  if (!navigator.mediaDevices || !window.MediaRecorder) { toast("Voice notes aren't supported on this device."); return false; }
  if (vn.state !== "idle") return false;
  vn.state = "starting";
  try { vn.stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true}}); }
  catch(e) { vn.state = "idle"; toast("ORDO needs the microphone for voice notes. Allow it when asked, or in your phone's settings → Apps → ORDO → Permissions."); return false; }
  if (!$("chatv")) { vn.stream.getTracks().forEach(t => t.stop()); vn.state = "idle"; return false; }
  const mime = REC_MIME();
  vn.rec = new MediaRecorder(vn.stream, mime ? {mimeType: mime, audioBitsPerSecond: 48000} : undefined);
  vn.chunks = []; vn.levels = []; vn.t0 = Date.now();
  vn.rec.ondataavailable = e => { if (e.data && e.data.size) vn.chunks.push(e.data); };
  vn.rec.start(200);
  try {
    vn.ctx = new (window.AudioContext || window.webkitAudioContext)();
    const an = vn.ctx.createAnalyser(); an.fftSize = 512; vn.ctx.createMediaStreamSource(vn.stream).connect(an);
    const buf = new Uint8Array(an.fftSize), cv = el.querySelector(".rwave"), cx = cv.getContext("2d");
    vn.sample = setInterval(() => {
      an.getByteTimeDomainData(buf); let s = 0; for (const v of buf) s += (v - 128) ** 2; vn.levels.push(Math.sqrt(s / buf.length));
      const W = cv.width, H = cv.height, n = Math.floor(W / 5), arr = vn.levels.slice(-n), mx = Math.max(6, ...arr);
      cx.clearRect(0, 0, W, H); cx.fillStyle = "#FF6E6A";
      arr.forEach((v, k) => { const h = Math.max(3, v / mx * H); cx.fillRect(W - (arr.length - k) * 5, (H - h) / 2, 3, h); });
    }, 70);
  } catch(e){}
  vn.state = "hold"; recUI(el, "hold");
  const rt = el.querySelector(".rt");
  vn.timer = setInterval(() => { const sec = (Date.now() - vn.t0) / 1000; rt.textContent = fmtSec(Math.floor(sec)); if (sec >= 300) stopRec(el, true); }, 200);
  try { navigator.vibrate && navigator.vibrate(25); } catch(e){}
  return true;
}
function setLock(el){ if (vn.state !== "hold") return; vn.state = "lock"; vn.lockAt = Date.now(); recUI(el, "lock"); try { navigator.vibrate && navigator.vibrate(15); } catch(e){} }
function recUI(el, mode){
  const snd = el.querySelector(".snd"), rec = el.querySelector(".rec"), row = el.querySelector(".crow"), lock = el.querySelector(".rlock");
  const on = mode !== "off";
  rec.hidden = !on; rec.classList.toggle("locked", mode === "lock");
  lock.hidden = mode !== "hold";
  row.querySelector("textarea").style.visibility = on ? "hidden" : "";
  row.querySelector(".att").style.visibility = on ? "hidden" : "";
  const cam2 = row.querySelector(".cam2"); if (cam2) cam2.style.visibility = on ? "hidden" : "";
  snd.classList.toggle("rec", mode === "hold");
  snd.innerHTML = mode === "lock" ? CI.send : CI.mic;
  snd.setAttribute("aria-label", mode === "lock" ? "Send voice note" : "Hold to record a voice note");
}
function stopRec(el, send){
  const r = vn.rec; if (!r || vn.state === "idle") return;
  vn.rec = null; vn.state = "idle"; clearInterval(vn.timer); clearInterval(vn.sample);
  const dur = (Date.now() - vn.t0) / 1000, levels = vn.levels.slice(), stream = vn.stream, ctx = vn.ctx;
  recUI(el, "off");
  const ta = el.querySelector("textarea"); if (ta) ta.dispatchEvent(new Event("input"));
  r.onstop = () => {
    stream.getTracks().forEach(t => t.stop()); try { ctx && ctx.close(); } catch(e){}
    if (!send) { toast("Voice note deleted."); return; }
    if (dur < 0.7 || !vn.chunks.length) { toast("Too short. Tap the mic to record, then Send."); return; }
    const blob = new Blob(vn.chunks, {type: (r.mimeType || "audio/webm").split(";")[0]});
    const N = 40, wave = []; for (let i = 0; i < N; i++) { const a = levels.slice(Math.floor(i * levels.length / N), Math.floor((i + 1) * levels.length / N)); wave.push(a.length ? Math.max(...a) : 0); }
    const mx = Math.max(1, ...wave);
    sendMedia(blob, "audio", {dur: Math.round(dur * 10) / 10, wave: wave.map(v => Math.round(v / mx * 31))}, "");
  };
  try { r.requestData(); } catch(e){}
  r.stop();
}
const audioBlobs = {};   // media url → local object URL: download once, then play from the phone
async function localAudio(src){
  if (src.startsWith("blob:")) return src;
  if (audioBlobs[src]) return audioBlobs[src];
  const r = await fetch(src); if (!r.ok) throw new Error("not ready");
  return (audioBlobs[src] = URL.createObjectURL(await r.blob()));
}
function voiceBubble(m, src){
  const w = document.createElement("div"); w.className = "vn";
  const wave = (m.media && m.media.wave) || Array.from({length: 40}, (_, i) => 8 + (i * 7) % 20);
  w.innerHTML = `<button class="vp" aria-label="Play">${CI.play}</button><div class="vw">${wave.map(v => `<i style="height:${Math.max(3, v / 31 * 26)}px"></i>`).join("")}</div><span class="vt">${fmtSec(Math.round((m.media && m.media.dur) || 0))}</span>`;
  const btn = w.querySelector(".vp"), bars = [...w.querySelectorAll(".vw i")], vt = w.querySelector(".vt"), total = (m.media && m.media.dur) || 0;
  const paint = (t, playing) => { const k = total ? t / total : 0; bars.forEach((b, i) => b.classList.toggle("on", i / bars.length < k)); vt.textContent = playing ? fmtSec(Math.floor(t)) + " / " + fmtSec(Math.round(total)) : fmtSec(Math.round(total)); btn.innerHTML = playing ? CI.pause : CI.play; };
  btn.onclick = async e => {
    e.stopPropagation();
    if (!vn.audio) vn.audio = new Audio();
    const a = vn.audio;
    if (vn.playing && vn.playing.src === src && !a.paused) { a.pause(); return; }
    btn.innerHTML = '<span class="spin"></span>';
    let url;
    for (let k = 0; k < 4 && !url; k++) { try { url = await localAudio(src); } catch(err) { await new Promise(r => setTimeout(r, 1200)); } }   // a brand-new note can take a moment to reach every server
    if (!url) { paint(0, false); return toast("Couldn't load that voice note. Check your connection."); }
    if (!vn.playing || vn.playing.src !== src) { if (vn.playing && vn.playing.paint) vn.playing.paint(0, false); a.src = url; }
    vn.playing = {src, paint};
    a.ontimeupdate = () => paint(a.currentTime, true); a.onpause = () => paint(a.currentTime, false); a.onended = () => { paint(0, false); vn.playing = null; };
    a.play().catch(() => { paint(0, false); toast("This phone can't play that voice note format."); });
  };
  if (vn.playing && vn.playing.src === src && vn.audio && !vn.audio.paused) { vn.playing.paint = paint; paint(vn.audio.currentTime, true); }
  return w;
}

// ---- ORDO camera in chat: tap = photo, hold = video
const cc = {stream: null, facing: "environment", rec: null, chunks: [], t0: 0, torch: false, raf: null, holdT: null};
const CC_MAX = 60;
async function chatCamera(el){
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return pickGallery(el);
  const c = document.createElement("div"); c.className = "cam ccam"; c.id = "ccam";
  c.innerHTML = `<video playsinline muted autoplay></video><div class="flash"></div>
    <div class="ctop"><button class="cbtn" data-a="close" aria-label="Close">✕</button><div class="ttl">ORDO camera<small>Tap for photo · hold for video</small></div><button class="cbtn" data-a="torch" aria-label="Flash" hidden>⚡</button></div>
    <div class="ccrec" hidden><span class="dotr"></span><span class="t">0:00</span></div>
    <div class="cbot"><button class="cbtn" data-a="gallery" aria-label="Gallery">${CAM_ICONS.gallery}</button>
      <button class="shutter ccs" data-a="shoot" aria-label="Tap for photo, hold for video"><svg viewBox="0 0 90 90"><circle cx="45" cy="45" r="40" fill="none" stroke="#F3F1EC" stroke-width="5"/><circle class="prog" cx="45" cy="45" r="40" fill="none" stroke="#7C8BFF" stroke-width="5" stroke-linecap="round" stroke-dasharray="0 252" transform="rotate(-90 45 45)"/><path class="seg" d="M56 10.6A36 36 0 0 1 79.4 34" fill="none" stroke="#7C8BFF" stroke-width="5" stroke-linecap="round"/><circle class="core" cx="45" cy="45" r="31" fill="#F3F1EC"/></svg></button>
      <button class="cbtn" data-a="flip" aria-label="Switch camera">${CAM_ICONS.flip}</button></div>`;
  el.appendChild(c);
  history.pushState({ccam: 1}, ""); window.addEventListener("popstate", ccBack);
  const q = a => c.querySelector(`[data-a=${a}]`);
  q("close").onclick = () => history.back();
  q("gallery").onclick = () => { ccClose(); history.back(); pickGallery(el); };
  q("flip").onclick = () => { if (cc.rec) return; cc.facing = cc.facing === "user" ? "environment" : "user"; ccStart(c); };
  q("torch").onclick = async () => { cc.torch = !cc.torch; try { await cc.stream.getVideoTracks()[0].applyConstraints({advanced: [{torch: cc.torch}]}); q("torch").classList.toggle("on", cc.torch); } catch(e){} };
  const sh = q("shoot");
  let held = false;
  sh.onpointerdown = e => { e.preventDefault(); try { sh.setPointerCapture(e.pointerId); } catch(_){} held = false; cc.holdT = setTimeout(() => { held = true; ccRecord(el, c); }, 260); };
  sh.onpointerup = sh.onpointercancel = () => { clearTimeout(cc.holdT); if (held) ccStopRecord(el, c); else ccPhoto(el, c); held = false; };
  await ccStart(c);
}
function ccBack(){ ccClose(); }
function ccClose(){
  window.removeEventListener("popstate", ccBack);
  if (cc.rec) { try { cc.rec.onstop = null; cc.rec.stop(); } catch(e){} cc.rec = null; }
  if (cc.stream) cc.stream.getTracks().forEach(t => t.stop()); cc.stream = null; cancelAnimationFrame(cc.raf);
  const c = $("ccam"); if (c) c.remove();
}
async function ccStart(c){
  if (cc.stream) cc.stream.getTracks().forEach(t => t.stop());
  const v = {facingMode: cc.facing, width: {ideal: 1920}, height: {ideal: 1080}};
  try { cc.stream = await navigator.mediaDevices.getUserMedia({video: v, audio: true}); }
  catch(e) { try { cc.stream = await navigator.mediaDevices.getUserMedia({video: v}); } catch(e2) { cc.stream = null; } }
  if (!cc.stream) { toast("ORDO can't open the camera. Allow camera access in your phone's settings."); ccClose(); history.back(); return; }
  const vid = c.querySelector("video"); vid.srcObject = cc.stream; vid.classList.toggle("mirror", cc.facing === "user"); vid.play().catch(() => {});
  let torch = false; try { torch = !!(cc.stream.getVideoTracks()[0].getCapabilities().torch); } catch(e){}
  c.querySelector("[data-a=torch]").hidden = !torch;
}
async function ccPhoto(el, c){
  if (!cc.stream) return;
  const v = c.querySelector("video"), track = cc.stream.getVideoTracks()[0];
  let src = null;
  if ("ImageCapture" in window) { try { src = await createImageBitmap(await new ImageCapture(track).takePhoto()); } catch(e) { src = null; } }
  const w = src ? src.width : v.videoWidth, h = src ? src.height : v.videoHeight;
  const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
  const x = cv.getContext("2d"); if (cc.facing === "user") { x.translate(w, 0); x.scale(-1, 1); }
  x.drawImage(src || v, 0, 0, w, h);
  const fl = c.querySelector(".flash"); fl.style.opacity = .85; setTimeout(() => fl.style.opacity = 0, 70);
  beep(1500, .04, .12);
  const blob = await new Promise(r => cv.toBlob(r, "image/jpeg", .92));
  ccClose(); history.back();
  setTimeout(() => openEditor(el, [new File([blob], `ORDO-${Date.now()}.jpg`, {type: "image/jpeg"})]), 60);
}
function ccRecord(el, c){
  if (!cc.stream || cc.rec) return;
  const mime = ["video/mp4;codecs=avc1,mp4a", "video/mp4", "video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"].find(t => MediaRecorder.isTypeSupported(t)) || "";
  try { cc.rec = new MediaRecorder(cc.stream, mime ? {mimeType: mime, videoBitsPerSecond: 2800000, audioBitsPerSecond: 96000} : undefined); }
  catch(e) { toast("This phone can't record video here."); return; }
  cc.chunks = []; cc.t0 = Date.now();
  cc.rec.ondataavailable = e => { if (e.data && e.data.size) cc.chunks.push(e.data); };
  cc.rec.start(500);
  c.classList.add("recording"); c.querySelector(".ccrec").hidden = false;
  const prog = c.querySelector(".prog"), t = c.querySelector(".ccrec .t");
  const tick = () => {
    const sec = (Date.now() - cc.t0) / 1000;
    prog.setAttribute("stroke-dasharray", `${(251.3 * Math.min(1, sec / CC_MAX)).toFixed(1)} 252`);
    t.textContent = fmtSec(Math.floor(sec));
    if (sec >= CC_MAX) return ccStopRecord(el, c);
    cc.raf = requestAnimationFrame(tick);
  };
  tick();
  try { navigator.vibrate && navigator.vibrate(30); } catch(e){}
}
function ccStopRecord(el, c){
  const r = cc.rec; if (!r) return;
  cc.rec = null; cancelAnimationFrame(cc.raf);
  const dur = (Date.now() - cc.t0) / 1000, type = (r.mimeType || "video/webm").split(";")[0];
  r.onstop = () => {
    const blob = new Blob(cc.chunks, {type});
    ccClose(); history.back();
    if (dur < 0.6 || !blob.size) return toast("Hold the shutter a little longer to record.");
    setTimeout(() => openEditor(el, [new File([blob], `ORDO-${Date.now()}.${type.includes("mp4") ? "mp4" : "webm"}`, {type})]), 60);
  };
  try { r.requestData(); } catch(e){}
  r.stop();
}

''')
rep("</style>\n</head>", r""".chatv .mentions .mnone{padding:12px 14px;font-size:13.5px;color:var(--muted)}
.chatv .rec{grid-template-columns:auto auto auto minmax(0,1fr) auto!important;gap:10px!important;padding:0 10px!important}
.chatv .rec .rtrash{display:none;width:36px;height:36px;border:0;background:none;color:var(--warn);cursor:pointer;place-content:center}
.chatv .rec .rtrash svg{width:22px;height:22px}
.chatv .rec.locked .rtrash{display:grid}
.chatv .rec.locked .hint{display:none}
.chatv .rec .rwave{width:100%;height:28px;min-width:0}
.chatv .rlock{position:absolute;right:16px;bottom:calc(env(safe-area-inset-bottom,0px) + 78px);width:40px;padding:10px 0 8px;border-radius:999px;background:#1a1d26;border:1px solid var(--line);display:grid;justify-items:center;gap:4px;color:var(--muted);animation:rlk 1.2s ease-in-out infinite}
.chatv .rlock[hidden]{display:none}
.chatv .rlock svg{width:18px;height:18px}.chatv .rlock span{font-size:10px}
@keyframes rlk{50%{transform:translateY(-6px)}}
.vn .vp .spin{width:16px;height:16px;border-radius:50%;border:2.5px solid currentColor;border-right-color:transparent;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.ccam{z-index:9}
.ccam .ccs{width:96px;height:96px;touch-action:none}
.ccam .ccs svg{width:96px;height:96px}
.ccam .ccs .core{transition:r .2s,fill .2s}
.ccam.recording .ccs .core{r:18;fill:#FF6E6A}
.ccam.recording .ccs .seg{opacity:0}
.ccam .ccrec{position:absolute;top:calc(env(safe-area-inset-top,0px) + 74px);left:50%;transform:translateX(-50%);z-index:4;display:flex;gap:8px;align-items:center;background:rgba(8,9,12,.6);border-radius:999px;padding:6px 14px;font-family:var(--f-mono);font-size:14px;color:#fff}
.ccam .ccrec .dotr{width:10px;height:10px;border-radius:50%;background:#FF6E6A;animation:blink 1s infinite}
.ccam .ccrec[hidden]{display:none}
.ccam .cbot{grid-template-columns:1fr auto 1fr}
.ccam .cbot [data-a=gallery]{justify-self:start;width:48px;height:48px;padding:0;justify-content:center}
.ccam .cbot [data-a=flip]{justify-self:end;width:48px;height:48px;padding:0;justify-content:center}
</style>
</head>""")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
