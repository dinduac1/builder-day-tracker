"""One-off: WhatsApp-style media in crew chat. 📎 opens the phone's photo/video grid at once; a camera button in the
composer; an editor before sending: photos (crop presets, rotate, draw, undo), videos (trim on a frame strip, mute),
big videos compressed to fit."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rep('''<button class="ib att" aria-label="Attach">${CI.clip}</button><textarea rows="1" maxlength="1000" placeholder="Message" aria-label="Message"></textarea><button class="snd"''',
    '''<button class="ib att" aria-label="Photos and videos">${CI.clip}</button><textarea rows="1" maxlength="1000" placeholder="Message" aria-label="Message"></textarea><button class="ib cam2" aria-label="Camera">${CI.camera}</button><button class="snd"''')
rep('''  const mode = () => { const typing = !!ta.value.trim();''', '''  const cam2 = el.querySelector(".cam2");
  const mode = () => { const typing = !!ta.value.trim(); cam2.hidden = typing;''')
rep('''  el.querySelector(".att").onclick = () => attachSheet(el);''', '''  el.querySelector(".att").onclick = () => pickGallery(el);
  cam2.onclick = () => cameraSheet(el);''')

i = s.index("function attachSheet(el){"); j = s.index("// ---- voice notes")
s = s[:i] + r'''/** 📎: the phone's photo & video grid straight away (several at once). */
function pickGallery(el){
  const i = document.createElement("input"); i.type = "file"; i.accept = "image/*,video/*"; i.multiple = true;
  i.onchange = () => i.files.length && openEditor(el, [...i.files]); i.click();
}
function cameraSheet(el){
  const cap = accept => { const i = document.createElement("input"); i.type = "file"; i.accept = accept; i.capture = "environment"; i.onchange = () => i.files.length && openEditor(el, [...i.files]); i.click(); };
  sheet(el, [[CI.camera, "Take a photo", () => cap("image/*")], [CI.video, "Record a video", () => cap("video/*")], [CI.photo, "Choose from gallery", () => pickGallery(el)]]);
}
const VIDEO_MAX = 25 * 1024 * 1024, VIDEO_MAX_LEN = 300;
const CROPS = [["orig", "Original", 0], ["1:1", "1:1", 1], ["4:5", "4:5", 4 / 5], ["9:16", "9:16", 9 / 16]];
const PEN = ["#F3F1EC", "#7C8BFF", "#FF6E6A", "#0A0C16"];
const EI = {
  crop: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 2v16h16M2 6h16v16"/></svg>',
  rot: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v5h-5"/></svg>',
  pen: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m4 20 1-5L16 4l4 4L9 19z"/><path d="m13 7 4 4"/></svg>',
  undo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/></svg>',
  mute: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"><path d="M4 9h4l5-4v14l-5-4H4z"/><path d="m17 9 4 6M21 9l-4 6"/></svg>',
  sound: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"><path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M17 8a5 5 0 0 1 0 8M19.5 5.5a8.5 8.5 0 0 1 0 13"/></svg>',
};
const mb = n => (n / 1048576).toFixed(n < 10485760 ? 1 : 0) + " MB";
/** Editor before sending: photos (crop, rotate, draw), videos (trim, mute). Caption goes with the first item. */
async function openEditor(el, files){
  files = files.filter(f => /^(image|video)\//.test(f.type)).slice(0, 30);
  if (!files.length) return toast("Photos and videos only.");
  const items = files.map(f => ({file: f, kind: f.type.startsWith("video/") ? "video" : "image", url: URL.createObjectURL(f), rot: 0, crop: 0, strokes: [], start: 0, end: null, dur: null, mute: false}));
  let cur = 0, drawing = false, pen = 1;
  const ed = document.createElement("div"); ed.className = "cprev cedit";
  ed.innerHTML = `<div class="pt"><button class="x" aria-label="Cancel">✕</button><div class="tools"></div></div>
    <div class="pm"></div><div class="pens" hidden></div><div class="strip" hidden></div>
    <div class="pb"><input maxlength="1000" placeholder="Add a caption…"><button aria-label="Send">${CI.send}</button></div><div class="busy" hidden><div></div></div>`;
  el.appendChild(ed);
  const pm = ed.querySelector(".pm"), tools = ed.querySelector(".tools"), pens = ed.querySelector(".pens"), strip = ed.querySelector(".strip");
  const close = () => { items.forEach(it => URL.revokeObjectURL(it.url)); ed.remove(); };
  ed.querySelector(".x").onclick = close;
  const tool = (icon, label, fn, on) => { const b = document.createElement("button"); b.className = "tb" + (on ? " on" : ""); b.innerHTML = icon; b.title = label; b.setAttribute("aria-label", label); b.onclick = fn; tools.appendChild(b); return b; };

  // ---- photos
  async function bmpOf(it){ if (!it.bmp) it.bmp = await createImageBitmap(it.file); return it.bmp; }
  function geometry(it, bmp){
    const sw = it.rot % 180 ? bmp.height : bmp.width, sh = it.rot % 180 ? bmp.width : bmp.height, r = CROPS[it.crop][2];
    let cw = sw, ch = sh;
    if (r) { if (sw / sh > r) cw = sh * r; else ch = sw / r; }
    return {sw, sh, cw, ch, ox: (sw - cw) / 2, oy: (sh - ch) / 2};
  }
  function paint(it, bmp, canvas, scale){
    const g = geometry(it, bmp);
    canvas.width = Math.round(g.cw * scale); canvas.height = Math.round(g.ch * scale);
    const x = canvas.getContext("2d"); x.imageSmoothingQuality = "high";
    x.save(); x.scale(scale, scale); x.translate(-g.ox, -g.oy);
    x.translate(g.sw / 2, g.sh / 2); x.rotate(it.rot * Math.PI / 180); x.drawImage(bmp, -bmp.width / 2, -bmp.height / 2); x.restore();
    x.lineCap = "round"; x.lineJoin = "round";
    it.strokes.forEach(st => { x.strokeStyle = st.c; x.lineWidth = st.w * Math.min(canvas.width, canvas.height); x.beginPath(); st.p.forEach(([u, v], k) => k ? x.lineTo(u * canvas.width, v * canvas.height) : x.moveTo(u * canvas.width, v * canvas.height)); if (st.p.length === 1) x.lineTo(st.p[0][0] * canvas.width + .1, st.p[0][1] * canvas.height); x.stroke(); });
  }
  async function showImage(it){
    const bmp = await bmpOf(it), c = document.createElement("canvas"), g = geometry(it, bmp);
    const fit = Math.min((pm.clientWidth - 16) / g.cw, (pm.clientHeight - 16) / g.ch, 1);
    paint(it, bmp, c, fit * (devicePixelRatio || 1)); c.style.width = Math.round(g.cw * fit) + "px"; c.style.height = Math.round(g.ch * fit) + "px";
    pm.innerHTML = ""; pm.appendChild(c);
    let st = null;
    c.onpointerdown = e => { if (!drawing) return; c.setPointerCapture(e.pointerId); const r = c.getBoundingClientRect(); st = {c: PEN[pen], w: .012, p: [[(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]]}; it.strokes.push(st); paint(it, bmp, c, fit * (devicePixelRatio || 1)); };
    c.onpointermove = e => { if (!st) return; const r = c.getBoundingClientRect(); st.p.push([(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]); paint(it, bmp, c, fit * (devicePixelRatio || 1)); };
    c.onpointerup = c.onpointercancel = () => { st = null; };
    c.style.touchAction = drawing ? "none" : "";
  }
  async function exportImage(it){
    const bmp = await bmpOf(it), g = geometry(it, bmp), k = Math.min(1, 1920 / Math.max(g.cw, g.ch)), c = document.createElement("canvas");
    paint(it, bmp, c, k);
    return {blob: await new Promise(r => c.toBlob(r, "image/jpeg", .88)), w: c.width, h: c.height};
  }

  // ---- videos
  async function showVideo(it){
    pm.innerHTML = `<div class="vwrap"><video playsinline loop></video><div class="vinfo"></div><div class="tl2"><div class="frames"></div><div class="dim l"></div><div class="dim r"></div><div class="win"><i class="h a"></i><i class="h b"></i></div></div></div>`;
    const v = pm.querySelector("video"), info = pm.querySelector(".vinfo"), tl = pm.querySelector(".tl2"), win = pm.querySelector(".win"), dl = pm.querySelector(".dim.l"), dr = pm.querySelector(".dim.r");
    v.src = it.url; v.muted = it.mute;
    await new Promise(r => { if (v.readyState >= 1) r(); else v.onloadedmetadata = r; v.onerror = r; });
    it.dur = isFinite(v.duration) ? v.duration : 0; if (it.end == null) it.end = Math.min(it.dur, VIDEO_MAX_LEN);
    v.currentTime = it.start; v.play().catch(() => {});
    v.ontimeupdate = () => { if (it.dur && v.currentTime >= it.end - .05) v.currentTime = it.start; };
    const paintTl = () => {
      if (!it.dur) { tl.hidden = true; info.textContent = mb(it.file.size); return; }
      const a = it.start / it.dur * 100, b = it.end / it.dur * 100;
      win.style.left = a + "%"; win.style.width = (b - a) + "%"; dl.style.width = a + "%"; dr.style.left = b + "%";
      const len = it.end - it.start, est = willEncode(it) ? Math.min(VIDEO_MAX, len * (bitrateFor(len) + 96000) / 8) : it.file.size;
      info.textContent = `${fmtSec(Math.floor(it.start))} → ${fmtSec(Math.round(it.end))} · ${Math.round(len)} s · ~${mb(est)}${it.mute ? " · muted" : ""}${len > VIDEO_MAX_LEN ? " · trim to 5 min or less" : ""}`;
    };
    paintTl();
    // frame strip
    (async () => {
      if (!it.dur) return;
      if (!it.frames) {
        it.frames = []; const tv = document.createElement("video"); tv.muted = true; tv.preload = "auto"; tv.src = it.url;
        await new Promise(r => { tv.onloadeddata = r; tv.onerror = r; });
        for (let k = 0; k < 8; k++) {
          tv.currentTime = Math.min(it.dur - .05, (k + .5) * it.dur / 8);
          await new Promise(r => { tv.onseeked = r; setTimeout(r, 1500); });
          const c = document.createElement("canvas"); c.width = 80; c.height = 80;
          const x = c.getContext("2d"), sc = Math.max(80 / (tv.videoWidth || 80), 80 / (tv.videoHeight || 80));
          x.drawImage(tv, (80 - tv.videoWidth * sc) / 2, (80 - tv.videoHeight * sc) / 2, tv.videoWidth * sc, tv.videoHeight * sc);
          it.frames.push(c.toDataURL("image/jpeg", .6));
        }
      }
      const fr = pm.querySelector(".frames"); if (fr) fr.innerHTML = it.frames.map(u => `<img alt="" src="${u}">`).join("");
    })();
    // drag the handles
    const drag = which => e => {
      e.preventDefault(); e.stopPropagation(); const r = tl.getBoundingClientRect(); v.pause();
      const move = ev => {
        const t = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)) * it.dur;
        if (which === "a") it.start = Math.min(t, it.end - 1); else it.end = Math.max(t, it.start + 1);
        v.currentTime = which === "a" ? it.start : it.end - .05; paintTl();
      };
      const up = () => { removeEventListener("pointermove", move); removeEventListener("pointerup", up); v.currentTime = it.start; v.play().catch(() => {}); };
      addEventListener("pointermove", move); addEventListener("pointerup", up);
    };
    pm.querySelector(".h.a").onpointerdown = drag("a"); pm.querySelector(".h.b").onpointerdown = drag("b");
    it.__paintTl = paintTl;
  }
  const willEncode = it => it.kind === "video" && it.dur && (it.start > .05 || it.end < it.dur - .1 || it.mute || it.file.size > VIDEO_MAX);
  const bitrateFor = len => Math.max(600000, Math.min(2500000, (VIDEO_MAX * 0.92 * 8) / Math.max(1, len) - 96000));

  // ---- toolbar, strip, switching
  async function show(){
    const it = items[cur];
    tools.innerHTML = ""; pens.hidden = true;
    if (it.kind === "image") {
      tool(EI.crop, "Crop: " + CROPS[it.crop][1], () => { it.crop = (it.crop + 1) % CROPS.length; toast("Crop: " + CROPS[it.crop][1]); show(); });
      tool(EI.rot, "Rotate", () => { it.rot = (it.rot + 90) % 360; show(); });
      tool(EI.pen, "Draw", () => { drawing = !drawing; show(); }, drawing);
      tool(EI.undo, "Undo", () => { it.strokes.pop(); show(); });
      if (drawing) { pens.hidden = false; pens.innerHTML = PEN.map((c, k) => `<button style="background:${c}" class="${k === pen ? "on" : ""}" data-k="${k}" aria-label="Colour"></button>`).join("");
        pens.querySelectorAll("button").forEach(b => b.onclick = () => { pen = +b.dataset.k; show(); }); }
      await showImage(it);
    } else {
      tool(it.mute ? EI.mute : EI.sound, it.mute ? "Sound off" : "Sound on", () => { it.mute = !it.mute; const v = pm.querySelector("video"); if (v) v.muted = it.mute; show(); }, it.mute);
      if (!pm.querySelector("video") || pm.dataset.cur != cur) await showVideo(it); else it.__paintTl && it.__paintTl();
    }
    pm.dataset.cur = cur;
    strip.hidden = items.length < 2;
    strip.innerHTML = "";
    items.forEach((x, k) => {
      const b = document.createElement("button"); b.className = k === cur ? "on" : "";
      b.innerHTML = x.kind === "video" ? `<video src="${x.url}" muted preload="metadata"></video><span>▶</span>` : `<img alt="" src="${x.url}">`;
      b.onclick = () => { if (k !== cur) { cur = k; drawing = false; pm.dataset.cur = ""; show(); } };
      strip.appendChild(b);
    });
  }
  await show();
  addEventListener("resize", () => ed.isConnected && items[cur].kind === "image" && show(), {once: true});

  // ---- send
  ed.querySelector(".pb button").onclick = async () => {
    const cap = ed.querySelector(".pb input").value, busy = ed.querySelector(".busy"), bar = busy.firstChild;
    const ac = new (window.AudioContext || window.webkitAudioContext)();   // created on the tap, so video sound can be re-recorded
    const ready = [];
    for (let k = 0; k < items.length; k++) {
      const it = items[k];
      try {
        if (it.kind === "image") { const o = await exportImage(it); ready.push([o.blob, "image", {w: o.w, h: o.h}]); continue; }
        if (it.dur == null) { const v = document.createElement("video"); v.src = it.url; await new Promise(r => { v.onloadedmetadata = r; v.onerror = r; }); it.dur = isFinite(v.duration) ? v.duration : 0; it.end = Math.min(it.dur, VIDEO_MAX_LEN); }
        if (it.dur && it.end - it.start > VIDEO_MAX_LEN) { toast("Trim videos to 5 minutes or less."); return; }
        if (willEncode(it)) {
          busy.hidden = false; bar.textContent = "Preparing video…";
          const out = await transcodeVideo(it, ac, f => { bar.textContent = `Preparing video${items.length > 1 ? ` ${k + 1} of ${items.length}` : ""}… ${Math.round(f * 100)}%`; });
          if (out.size > VIDEO_MAX) { busy.hidden = true; toast("Still over 25 MB. Trim it shorter."); return; }
          ready.push([out, "video", {w: it.w || 0, h: it.h || 0, dur: Math.round((it.end - it.start) * 10) / 10}]);
        } else {
          if (it.file.size > VIDEO_MAX) { toast("Videos up to 25 MB. Trim it shorter."); return; }
          ready.push([it.file, "video", {w: 0, h: 0, dur: it.dur || 0}]);
        }
      } catch(e) { busy.hidden = true; toast(e.message || "Couldn't prepare that."); return; }
    }
    try { ac.close(); } catch(e){}
    close();
    ready.forEach(([blob, kind, extra], k) => sendMedia(blob, kind, extra, k === 0 ? cap : ""));
  };
}
/** Re-record the chosen part of a video (trim / mute / shrink to fit) in real time, as WebM. */
function transcodeVideo(it, ac, onProgress){
  return new Promise(async (res, rej) => {
    const v = document.createElement("video"); v.src = it.url; v.playsInline = true; v.preload = "auto";
    v.style.cssText = "position:fixed;left:-9999px;width:2px;height:2px";
    document.body.appendChild(v);
    try {
      await new Promise((r, j) => { v.onloadedmetadata = r; v.onerror = () => j(new Error("ORDO can't read that video.")); });
      it.w = v.videoWidth; it.h = v.videoHeight;
      const dest = ac.createMediaStreamDestination(); ac.createMediaElementSource(v).connect(dest); await ac.resume().catch(() => {});
      v.currentTime = it.start; await new Promise(r => { v.onseeked = r; setTimeout(r, 2000); });
      await v.play();
      const vs = v.captureStream ? v.captureStream() : v.mozCaptureStream();
      const tracks = [...vs.getVideoTracks()]; if (!it.mute) tracks.push(...dest.stream.getAudioTracks());
      const mime = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm"].find(t => MediaRecorder.isTypeSupported(t));
      const len = it.end - it.start;
      const rec = new MediaRecorder(new MediaStream(tracks), {mimeType: mime, videoBitsPerSecond: Math.round(Math.max(600000, Math.min(2500000, (25 * 1024 * 1024 * .92 * 8) / Math.max(1, len) - 96000))), audioBitsPerSecond: 96000});
      const chunks = []; rec.ondataavailable = e => e.data.size && chunks.push(e.data);
      rec.onstop = () => { v.remove(); res(new Blob(chunks, {type: "video/webm"})); };
      rec.start(500);
      const tick = () => {
        if (v.currentTime >= it.end - .03 || v.ended) { v.pause(); if (rec.state !== "inactive") rec.stop(); return; }
        onProgress && onProgress(Math.min(1, (v.currentTime - it.start) / Math.max(.1, len)));
        requestAnimationFrame(tick);
      };
      tick();
    } catch(e) { v.remove(); rej(e); }
  });
}
''' + s[j:]

rep("</style>\n</head>", r""".chatv .crow{grid-template-columns:44px minmax(0,1fr) auto 48px}
.chatv .cam2[hidden]{display:none}
.cedit{grid-template-rows:auto minmax(0,1fr) auto auto auto}
.cedit .pt{gap:8px}
.cedit .tools{display:flex;gap:6px}
.cedit .tb{width:42px;height:42px;border-radius:50%;border:0;background:rgba(255,255,255,.1);color:#fff;display:grid;place-content:center;cursor:pointer}
.cedit .tb svg{width:21px;height:21px}
.cedit .tb.on{background:#7C8BFF;color:#0A0C16}
.cedit .pm{position:relative}
.cedit .pm canvas{display:block;border-radius:6px}
.cedit .pens{display:flex;justify-content:center;gap:12px;padding:8px}
.cedit .pens button{width:28px;height:28px;border-radius:50%;border:2px solid rgba(255,255,255,.25);cursor:pointer}
.cedit .pens button.on{border-color:#fff;transform:scale(1.15)}
.cedit .strip{display:flex;gap:6px;overflow-x:auto;padding:6px 10px}
.cedit .strip button{flex:none;width:52px;height:52px;border-radius:10px;overflow:hidden;border:2px solid transparent;padding:0;background:#111;position:relative;cursor:pointer}
.cedit .strip button.on{border-color:#7C8BFF}
.cedit .strip img,.cedit .strip video{width:100%;height:100%;object-fit:cover}
.cedit .strip span{position:absolute;inset:0;display:grid;place-content:center;color:#fff;font-size:12px;text-shadow:0 1px 4px #000}
.cedit .vwrap{display:grid;gap:10px;width:min(100%,520px);justify-items:center}
.cedit .vwrap video{max-width:100%;max-height:52vh;border-radius:10px;background:#000}
.cedit .vinfo{font-family:var(--f-mono);font-size:12px;color:rgba(255,255,255,.8)}
.cedit .tl2{position:relative;width:100%;height:56px;border-radius:10px;overflow:hidden;background:#1a1d26;touch-action:none}
.cedit .tl2 .frames{position:absolute;inset:0;display:flex}.cedit .tl2 .frames img{flex:1;min-width:0;height:100%;object-fit:cover}
.cedit .tl2 .dim{position:absolute;top:0;bottom:0;background:rgba(0,0,0,.62)}.cedit .tl2 .dim.l{left:0}.cedit .tl2 .dim.r{right:0}
.cedit .tl2 .win{position:absolute;top:0;bottom:0;border:3px solid #7C8BFF;border-radius:8px;box-sizing:border-box}
.cedit .tl2 .h{position:absolute;top:-3px;bottom:-3px;width:18px;background:#7C8BFF;cursor:ew-resize;touch-action:none}
.cedit .tl2 .h.a{left:-9px;border-radius:8px 0 0 8px}.cedit .tl2 .h.b{right:-9px;border-radius:0 8px 8px 0}
.cedit .tl2 .h::after{content:"";position:absolute;left:7px;top:35%;bottom:35%;width:3px;border-radius:2px;background:#0A0C16}
.cedit .busy{position:absolute;inset:0;z-index:3;background:rgba(0,0,0,.72);display:grid;place-content:center;color:#fff;font-family:var(--f-mono);font-size:13px}
</style>
</head>""")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
