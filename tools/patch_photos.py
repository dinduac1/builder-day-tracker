"""One-off: progress photos. ORDO's own camera screen (guide, grid, timer, flip, full resolution), photos saved to
the phone's gallery and privately to the account, a progress gallery (Day 1 vs latest), and reports sent with the photo."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()

def rep(a, b):
    global s
    assert s.count(a) == 1, f"{s.count(a)} matches: " + a[:90]
    s = s.replace(a, b)

rep("</style>\n</head>", r""".cam{position:fixed;inset:0;z-index:90;background:#000;color:#F3F1EC;display:grid;grid-template-rows:auto 1fr auto;overflow:hidden;font-family:var(--f-body)}
.cam video,.cam .shot{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:#000}
.cam .shot{object-fit:contain}
.cam video.mirror{transform:scaleX(-1)}
.cam .ctop{position:relative;z-index:3;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;padding:calc(env(safe-area-inset-top,0px) + 14px) 14px 26px;background:linear-gradient(rgba(0,0,0,.6),transparent)}
.cam .ctop > :last-child{justify-self:end}
.cam .cbtn{border:1px solid rgba(243,241,236,.22);background:rgba(8,9,12,.42);-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);color:#F3F1EC;border-radius:999px;padding:9px 14px;font:inherit;font-size:13px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.cam .cbtn.on{background:#7C8BFF;border-color:#7C8BFF;color:#0A0C16}
.cam .cbtn svg{width:18px;height:18px}
.cam .ttl{font-family:var(--f-display);font-weight:800;letter-spacing:.16em;text-transform:uppercase;font-size:15px;text-align:center;line-height:1.15}
.cam .ttl small{display:block;font-family:var(--f-mono);font-weight:400;letter-spacing:.12em;font-size:10px;color:rgba(243,241,236,.62);margin-top:3px}
.cam .guide{position:absolute;inset:0;z-index:1;pointer-events:none}
.cam .guide svg{width:100%;height:100%}
.cam .cbot{position:relative;z-index:3;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:10px;padding:30px 20px calc(env(safe-area-inset-bottom,0px) + 26px);background:linear-gradient(transparent,rgba(0,0,0,.7))}
.cam .cbot > :first-child{justify-self:start}.cam .cbot > :last-child{justify-self:end}
.cam .shutter{width:82px;height:82px;border-radius:50%;border:0;background:none;padding:0;cursor:pointer;display:grid;place-content:center}
.cam .shutter:active{transform:scale(.94)}
.cam .shutter svg{width:82px;height:82px}
.cam .tseg{display:flex;gap:4px;justify-content:center;margin-bottom:14px;grid-column:1 / -1}
.cam .count{position:absolute;inset:0;z-index:4;display:grid;place-content:center;font-family:var(--f-display);font-size:180px;font-weight:800;color:#F3F1EC;text-shadow:0 6px 40px rgba(0,0,0,.6);pointer-events:none}
.cam .flash{position:absolute;inset:0;background:#fff;opacity:0;z-index:5;pointer-events:none;transition:opacity .35s}
.cam .cmsg{position:relative;z-index:3;align-self:center;justify-self:center;max-width:300px;text-align:center;display:grid;gap:14px;padding:20px}
.cam .keep{background:#F3F1EC;color:#08090C;border-color:#F3F1EC;padding:13px 22px;font-size:15px}
.gthumb{width:64px;height:84px;border-radius:12px;object-fit:cover;border:1px solid var(--line);cursor:pointer}
.photocmp{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.photocmp figure{margin:0;display:grid;gap:6px}
.photocmp img{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:16px;border:1px solid var(--line);background:var(--sunk)}
.photocmp figcaption,.pgrid figcaption{font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.pgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.pgrid figure{margin:0;display:grid;gap:4px;cursor:pointer}
.pgrid img{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:12px;border:1px solid var(--line)}
.pfull{width:100%;max-height:70vh;object-fit:contain;border-radius:16px;background:#000}
.sheet .shimg{display:grid;grid-template-columns:56px minmax(0,1fr) auto;gap:12px;align-items:center;padding:8px;border:1px solid var(--line);border-radius:14px;background:var(--bg)}
.sheet .shimg img{width:56px;height:72px;object-fit:cover;border-radius:10px}
.sheet .shimg input{appearance:none;width:44px;height:26px;border-radius:999px;background:var(--line-strong);position:relative;cursor:pointer;margin:0}
.sheet .shimg input::after{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;transition:left .15s}
.sheet .shimg input:checked{background:var(--accent)}.sheet .shimg input:checked::after{left:21px}
</style>
</head>""")

# goal rows: the progress photo rule gets the camera
rep('''    if (g.workout) {
      const acts = document.createElement("div"); acts.className = "gacts";''', '''    if (isPhotoGoal(g)) {
      const acts = document.createElement("div"); acts.className = "gacts";
      if (photoCache[sel] === undefined) loadPhoto(sel);
      const th = photoCache[sel];
      if (th) { const im = document.createElement("img"); im.className = "gthumb"; im.alt = "Today's progress photo"; im.src = th; im.onclick = () => openPhotos(sel); acts.appendChild(im); }
      if (sel <= today) {
        const tk = document.createElement("button"); tk.className = "linkbtn gwork"; tk.textContent = th ? "Retake photo" : "📷 Take your progress photo";
        tk.onclick = () => openCamera(sel); acts.appendChild(tk);
      }
      const all = document.createElement("button"); all.className = "linkbtn"; all.textContent = "All progress photos";
      all.onclick = () => openPhotos(); acts.appendChild(all);
      row.appendChild(acts);
    }
    if (g.workout) {
      const acts = document.createElement("div"); acts.className = "gacts";''')

# reports go out with the day's photo
rep('''function openShare(k){
  shareSheet({''', '''async function openShare(k){
  const image = photoCache[k] !== undefined ? photoCache[k] : await photoStore.get(k).catch(() => null);
  shareSheet({image, ''')
rep('''  sh.querySelector("h3").textContent = o.title;''', '''  sh.querySelector("h3").textContent = o.title;
  let withImg = !!o.image;
  if (o.image) {
    const box = document.createElement("label"); box.className = "shimg";
    box.innerHTML = `<img alt=""><div><b>Progress photo</b><div class="beat" style="margin:2px 0 0">Sent with your report</div></div><input type="checkbox" checked aria-label="Send the progress photo">`;
    box.querySelector("img").src = o.image;
    box.querySelector("input").onchange = e => { withImg = e.target.checked; };
    sh.querySelector(".fl").before(box);
  }''')
rep('''        NATIVE.shareTo(t.pkg, WA_PKGS.includes(t.pkg) ? waText : t.pkg === "org.telegram.messenger" ? o.text : (/sms|messag|mms/i.test(t.pkg) ? smsText : o.text), phone);''',
    '''        const txt = WA_PKGS.includes(t.pkg) ? waText : /sms|messag|mms/i.test(t.pkg) ? smsText : o.text;
        if (withImg && o.image && NATIVE.shareImageTo) NATIVE.shareImageTo(t.pkg, txt, phone, o.image);
        else NATIVE.shareTo(t.pkg, txt, phone);''')
rep('''      if (NATIVE && NATIVE.share) NATIVE.share(o.text, o.subject || o.title); else navigator.share({text: o.text}).catch(() => {});''',
    '''      if (NATIVE && NATIVE.share) return NATIVE.share(o.text, o.subject || o.title);
      (async () => {
        let files = [];
        if (withImg && o.image) { try { const b = await (await fetch(o.image)).blob(); files = [new File([b], "ORDO-progress.jpg", {type: "image/jpeg"})]; } catch(e){} }
        const data = files.length && navigator.canShare && navigator.canShare({files}) ? {text: o.text, files} : {text: o.text};
        navigator.share(data).catch(() => {});
      })();''')
rep('''    if (navigator.share) note.textContent = "Two WhatsApps on this phone? Tap Choose app to pick the right one.";''',
    '''    if (navigator.share) note.textContent = o.image ? "Tap Choose app to send the photo too, or to pick between two WhatsApps." : "Two WhatsApps on this phone? Tap Choose app to pick the right one.";''')

# a new sign-in sees its own photos
rep('''    unwatchHosted();''', '''    unwatchHosted(); photoCache = {};''')

rep("/* =========================================================== notification settings */", r'''/* =========================================================== progress photos */
const isPhotoGoal = g => g.id === "photo" || g.icon === "camera";
let photoCache = {};   // dateKey -> data URL | null (looked up, none) ; missing = not looked up yet
// Signed in: users/{uid}/photos/{date} (private, synced, cached offline by Firestore). Signed out: this browser (IndexedDB).
const idb = (() => {
  let dbp = null;
  const open = () => dbp || (dbp = new Promise((res, rej) => { const r = indexedDB.open("ordo-photos", 1); r.onupgradeneeded = () => r.result.createObjectStore("p"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); }));
  const tx = (mode, fn) => open().then(db => new Promise((res, rej) => { const t = db.transaction("p", mode), st = t.objectStore("p"), out = fn(st); t.oncomplete = () => res(out && out.result); t.onerror = () => rej(t.error); }));
  return {
    get: k => tx("readonly", st => st.get(k)),
    put: (k, v) => tx("readwrite", st => st.put(v, k)),
    del: k => tx("readwrite", st => st.delete(k)),
    all: () => open().then(db => new Promise((res, rej) => { const out = [], r = db.transaction("p").objectStore("p").openCursor(); r.onsuccess = () => { const c = r.result; if (c) { out.push({k: c.key, img: c.value.img}); c.continue(); } else res(out); }; r.onerror = () => rej(r.error); })),
  };
})();
const photoStore = {
  col(){ const fs = crewFS(); return fs ? fs.db.collection("users").doc(fs.uid).collection("photos") : null; },
  async get(k){ const c = this.col(); if (c) { const d = await c.doc(k).get(); return d.exists ? d.data().img : null; } const v = await idb.get(k); return v ? v.img : null; },
  async put(k, img){ const v = {img, ts: Date.now()}, c = this.col(); return c ? c.doc(k).set(v) : idb.put(k, v); },
  async del(k){ const c = this.col(); return c ? c.doc(k).delete() : idb.del(k); },
  async list(){ const c = this.col(); const L = c ? (await c.get()).docs.map(d => ({k: d.id, img: d.data().img})) : await idb.all(); return L.filter(x => x.img).sort((a, b) => a.k < b.k ? -1 : 1); },
};
function loadPhoto(k){
  photoCache[k] = null;
  photoStore.get(k).then(v => { if (v) { photoCache[k] = v; render(); } }).catch(() => {});
}
function canvasJpeg(src, maxSide, q){
  const w0 = src.width, h0 = src.height, k = Math.min(1, maxSide / Math.max(w0, h0));
  const c = document.createElement("canvas"); c.width = Math.round(w0 * k); c.height = Math.round(h0 * k);
  const x = c.getContext("2d"); x.imageSmoothingQuality = "high"; x.drawImage(src, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", q);
}
/** Full-resolution copy to the phone's gallery (Pictures/ORDO); the website downloads it. */
function saveToDevice(dataUrl, name){
  if (NATIVE && NATIVE.savePhoto) { const err = NATIVE.savePhoto(dataUrl, name); if (err) toast("Couldn't save to your gallery: " + err); return !err; }
  const a = document.createElement("a"); a.href = dataUrl; a.download = name; document.body.appendChild(a); a.click(); a.remove(); return true;
}
async function keepPhoto(k, canvas){
  const full = canvas.toDataURL("image/jpeg", .93);
  const label = challengeState(keyOf(new Date())) && settings.challenge ? `Day${daysBetween(settings.challenge.start, k) + 1}-` : "";
  saveToDevice(full, `ORDO-${label}${k}.jpg`);
  // the synced copy: sharp at phone size, small enough for the account (under ~900 KB)
  let cloud = canvasJpeg(canvas, 1600, .88);
  for (const [side, q] of [[1600, .8], [1400, .8], [1200, .78]]) { if (cloud.length < 1.2e6) break; cloud = canvasJpeg(canvas, side, q); }
  photoCache[k] = cloud;
  try { await photoStore.put(k, cloud); } catch(e) { toast("Saved to your phone. ORDO couldn't store it: " + (e.message || e)); }
  const pg = goalsList().find(isPhotoGoal);
  const prevSel = sel; sel = k;
  if (pg && !goalDone(pg, goalVal(k, pg))) setGoal(pg.id, true); else render();
  sel = prevSel; render();
  toast("Progress photo saved to your phone and to ORDO.");
}

const camState = {stream: null, facing: "user", timer: 0, guide: true, k: null, busy: false};
const CAM_ICONS = {
  flip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h3l2-3h8l2 3h3v12H3z"/><path d="M9.5 13.5a2.5 2.5 0 0 1 4.3-1.8M14.5 13.5a2.5 2.5 0 0 1-4.3 1.8"/><path d="M14 10.5v1.4h-1.4M10 16.5v-1.4h1.4"/></svg>',
  gallery: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.8"/><path d="m4 18 5-5 4 4 3-3 4 4"/></svg>',
  shutter: '<svg viewBox="0 0 82 82"><circle cx="41" cy="41" r="37" fill="none" stroke="#F3F1EC" stroke-width="5"/><path d="M50.6 8.6A33 33 0 0 1 72.4 30" fill="none" stroke="#7C8BFF" stroke-width="5" stroke-linecap="round"/><circle cx="41" cy="41" r="29" fill="#F3F1EC"/></svg>',
};
const GUIDE_SVG = `<svg viewBox="0 0 100 100" preserveAspectRatio="none"><g stroke="rgba(243,241,236,.16)" stroke-width=".25" vector-effect="non-scaling-stroke"><path d="M33.3 0v100M66.6 0v100M0 33.3h100M0 66.6h100"/></g></svg>
  <svg viewBox="0 0 100 180" style="position:absolute;inset:12% 0 10%;height:78%;width:100%" preserveAspectRatio="xMidYMid meet"><g fill="none" stroke="rgba(243,241,236,.42)" stroke-width="1.1" stroke-dasharray="3 3" stroke-linejoin="round">
  <ellipse cx="50" cy="22" rx="10" ry="12.5"/><path d="M41 34c-1 3-2 5-2 7M59 34c1 3 2 5 2 7"/>
  <path d="M30 46c3-4 11-5 20-5s17 1 20 5l6 32c1 5-1 7-3 7l-4-25-2 26 3 38-5 52h-8l-3-50h-8l-3 50h-8l-5-52 3-38-2-26-4 25c-2 0-4-2-3-7z"/></g></svg>`;
function openCamera(k, samePage){
  camState.k = k;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return pickPhotoFile(k);
  const el = document.createElement("div"); el.className = "cam"; el.id = "cam";
  const cs = settings.challenge && settings.challenge.start ? daysBetween(settings.challenge.start, k) + 1 : null;
  el.innerHTML = `<video playsinline muted autoplay></video><div class="guide"></div><div class="count" hidden></div><div class="flash"></div>
    <div class="ctop"><button class="cbtn" data-a="close">✕</button><div class="ttl">Progress photo<small>${cs && cs > 0 ? `${esc((settings.challenge || {}).name || "Day")} · Day ${cs}` : esc(shortDate(k))}</small></div><button class="cbtn" data-a="guide">Guide</button></div>
    <div></div>
    <div class="cbot"><div class="tseg"><button class="cbtn" data-t="0">No timer</button><button class="cbtn" data-t="3">3s</button><button class="cbtn" data-t="10">10s</button></div>
      <button class="cbtn" data-a="gallery" aria-label="Choose from gallery">${CAM_ICONS.gallery}</button><button class="shutter" data-a="shoot" aria-label="Take photo">${CAM_ICONS.shutter}</button><button class="cbtn" data-a="flip" aria-label="Switch camera">${CAM_ICONS.flip}</button></div>`;
  document.body.appendChild(el);
  if (!samePage) history.pushState({cam: 1}, "");   // the phone's Back closes the camera
  window.addEventListener("popstate", camBack);
  const q = a => el.querySelector(`[data-a=${a}]`);
  q("close").onclick = () => history.back();
  q("flip").onclick = () => { camState.facing = camState.facing === "user" ? "environment" : "user"; startCam(); };
  q("gallery").onclick = () => { closeCamera(); pickPhotoFile(k); };
  q("shoot").onclick = shoot;
  const g = q("guide"); const showGuide = () => { el.querySelector(".guide").innerHTML = camState.guide ? GUIDE_SVG : ""; g.classList.toggle("on", camState.guide); };
  g.onclick = () => { camState.guide = !camState.guide; showGuide(); }; showGuide();
  el.querySelectorAll("[data-t]").forEach(b => { b.classList.toggle("on", +b.dataset.t === camState.timer); b.onclick = () => { camState.timer = +b.dataset.t; el.querySelectorAll("[data-t]").forEach(x => x.classList.toggle("on", x === b)); }; });
  startCam();
}
function camBack(){ closeCamera(true); }
function stopStream(){ if (camState.stream) camState.stream.getTracks().forEach(t => t.stop()); camState.stream = null; }
function closeCamera(fromBack){
  stopStream(); window.removeEventListener("popstate", camBack);
  const el = $("cam"); if (el) el.remove();
  if (!fromBack && history.state && history.state.cam) history.back();
}
async function startCam(){
  const el = $("cam"); if (!el) return;
  stopStream();
  const v = el.querySelector("video");
  try {
    camState.stream = await navigator.mediaDevices.getUserMedia({audio: false, video: {facingMode: camState.facing, width: {ideal: 3840}, height: {ideal: 2160}}});
    v.srcObject = camState.stream; v.classList.toggle("mirror", camState.facing === "user");
    await v.play().catch(() => {});
  } catch(e) {
    const mid = el.children[el.children.length - 2];
    mid.className = "cmsg"; mid.innerHTML = `<b style="font-size:18px">ORDO can't open the camera.</b><span style="color:rgba(243,241,236,.7)">Allow camera access for ORDO in your phone's settings, or pick a photo you've already taken.</span><button class="cbtn keep">Choose from gallery</button>`;
    mid.querySelector("button").onclick = () => { const k = camState.k; closeCamera(); pickPhotoFile(k); };
  }
}
async function shoot(){
  const el = $("cam"); if (!el || camState.busy || !camState.stream) return;
  camState.busy = true;
  const cnt = el.querySelector(".count");
  for (let n = camState.timer; n > 0; n--) { cnt.hidden = false; cnt.textContent = n; beep(n === 1 ? 1100 : 760, .09, .2); await new Promise(r => setTimeout(r, 1000)); if (!$("cam")) return; }
  cnt.hidden = true;
  const v = el.querySelector("video"), track = camState.stream.getVideoTracks()[0];
  let src = null;
  if ("ImageCapture" in window) { try { src = await createImageBitmap(await new ImageCapture(track).takePhoto()); } catch(e) { src = null; } }
  const w = src ? src.width : v.videoWidth, h = src ? src.height : v.videoHeight;
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d");
  if (camState.facing === "user") { x.translate(w, 0); x.scale(-1, 1); }   // keep it as you saw it
  x.drawImage(src || v, 0, 0, w, h);
  const fl = el.querySelector(".flash"); fl.style.opacity = .85; setTimeout(() => fl.style.opacity = 0, 60);
  camState.busy = false;
  reviewShot(c);
}
function reviewShot(c){
  const el = $("cam"); if (!el) return;
  stopStream();
  el.querySelector("video").remove(); el.querySelector(".guide").innerHTML = "";
  const img = document.createElement("img"); img.className = "shot"; img.alt = "Your photo"; img.src = c.toDataURL("image/jpeg", .9); el.prepend(img);
  const bot = el.querySelector(".cbot");
  bot.innerHTML = `<button class="cbtn" data-a="retake">Retake</button><span style="font-family:var(--f-mono);font-size:11px;color:rgba(243,241,236,.6)">${c.width}×${c.height}</span><button class="cbtn keep" data-a="keep">Use photo</button>`;
  bot.querySelector("[data-a=retake]").onclick = () => { window.removeEventListener("popstate", camBack); el.remove(); openCamera(camState.k, true); };
  bot.querySelector("[data-a=keep]").onclick = async () => { const k = camState.k; closeCamera(); await keepPhoto(k, c); };
}
function pickPhotoFile(k){
  const inp = document.createElement("input"); inp.type = "file"; inp.accept = "image/*";
  inp.onchange = async () => {
    const f = inp.files && inp.files[0]; if (!f) return;
    try {
      const bmp = await createImageBitmap(f);
      const c = document.createElement("canvas"); c.width = bmp.width; c.height = bmp.height; c.getContext("2d").drawImage(bmp, 0, 0);
      await keepPhoto(k, c);
    } catch(e) { toast("That file isn't a photo ORDO can read."); }
  };
  inp.click();
}
async function openPhotos(focusK){
  const o = openOverlay();
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">Progress photos</span><button class="close">✕ Close</button></div>
    <h2 class="exname">Progress</h2><p class="beat">Private to you. Every photo is also saved in your phone's gallery (Pictures › ORDO).</p><div id="phBody"><p class="beat">Loading…</p></div></div>`;
  o.querySelector(".close").onclick = () => closeOverlay();
  let L = [];
  try { L = await photoStore.list(); } catch(e) {}
  const body = o.querySelector("#phBody"); body.innerHTML = "";
  const c = settings.challenge, dayLbl = k => c && c.start && k >= c.start ? `Day ${daysBetween(c.start, k) + 1}` : shortDate(k);
  if (!L.length) {
    body.innerHTML = `<p class="beat">No photos yet. Take your first one: it becomes Day 1 of your before-and-after.</p>`;
    const b = document.createElement("button"); b.className = "btn primary block"; b.textContent = "📷 Take today's photo"; b.onclick = () => { closeOverlay(); openCamera(keyOf(new Date())); };
    body.appendChild(b); return;
  }
  const full = x => {
    body.innerHTML = `<img class="pfull" alt=""><div class="redfoot" style="padding-top:12px"><button class="btn-sm">Save to phone</button><button class="linkbtn">← All photos</button><button class="linkbtn" style="color:var(--warn)">Delete</button></div>`;
    body.querySelector("img").src = x.img;
    const [sv, back, del] = body.querySelectorAll("button");
    sv.onclick = () => saveToDevice(x.img, `ORDO-${x.k}.jpg`) && toast("Saved to your phone.");
    back.onclick = () => openPhotos();
    del.onclick = async () => { if (!del.dataset.sure) { del.dataset.sure = 1; del.textContent = "Tap again to delete"; return; } await photoStore.del(x.k).catch(() => {}); delete photoCache[x.k]; openPhotos(); render(); };
  };
  if (L.length > 1) {
    const a = L[0], b = L[L.length - 1], cmp = document.createElement("div"); cmp.className = "photocmp";
    cmp.innerHTML = `<figure><img alt=""><figcaption></figcaption></figure><figure><img alt=""><figcaption></figcaption></figure>`;
    const [i1, i2] = cmp.querySelectorAll("img"), [c1, c2] = cmp.querySelectorAll("figcaption");
    i1.src = a.img; i2.src = b.img; c1.textContent = "First · " + dayLbl(a.k); c2.textContent = "Latest · " + dayLbl(b.k);
    i1.onclick = () => full(a); i2.onclick = () => full(b);
    body.appendChild(cmp);
  }
  const t = document.createElement("div"); t.className = "rgtitle"; t.textContent = `${L.length} photo${L.length > 1 ? "s" : ""}`; body.appendChild(t);
  const grid = document.createElement("div"); grid.className = "pgrid";
  [...L].reverse().forEach(x => { const f = document.createElement("figure"); f.innerHTML = `<img alt="" loading="lazy"><figcaption></figcaption>`; f.querySelector("img").src = x.img; f.querySelector("figcaption").textContent = dayLbl(x.k); f.onclick = () => full(x); grid.appendChild(f); });
  body.appendChild(grid);
  if (focusK) { const x = L.find(y => y.k === focusK); if (x) full(x); }
}

/* =========================================================== notification settings */''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
