"""One-off: ORDO gallery screen in crew chat (app): camera tile + the phone's photos/videos, newest first, numbered
multi-select, Photos/Videos filter, then the editor. Website keeps the phone's own picker."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(ROOT, "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
rep('''/** 📎: the phone's photo & video grid straight away (several at once). */
function pickGallery(el){''', r'''/** 📎: in the app, ORDO's own gallery; on the website, the phone's picker. */
function pickGallery(el){
  if (!(NATIVE && NATIVE.galleryPage)) return pickFiles(el);
  const acc = NATIVE.galleryAccess();
  if (acc !== "none") return openGallery(el, acc);
  window.__ordoGalleryPerm = st => st === "none" ? galleryDenied(el) : openGallery(el, st);
  NATIVE.askGallery();
}
function galleryDenied(el){
  sheet(el, [[CI.photo, "Allow ORDO to see your photos", () => NATIVE.openAppSettings()], [CI.clip, "Pick with the phone's picker instead", () => pickFiles(el)]]);
}
function openGallery(el, access){
  const g = document.createElement("div"); g.className = "cgal"; g.id = "cgal";
  g.innerHTML = `<div class="gh"><button class="x" aria-label="Close">✕</button><b>Gallery</b><div class="seg2"><button data-k="all" class="on">All</button><button data-k="image">Photos</button><button data-k="video">Videos</button></div></div>
    ${access === "partial" ? `<button class="gpart">You've let ORDO see only some photos. <u>Allow all</u></button>` : ""}
    <div class="gg"></div><div class="gbar" hidden><span></span><button class="btn primary">Next →</button></div>`;
  el.appendChild(g);
  history.pushState({cgal: 1}, ""); window.addEventListener("popstate", galBack);
  const grid = g.querySelector(".gg"), bar = g.querySelector(".gbar");
  let kind = "all", offset = 0, done = false, loading = false; const picked = [];
  g.querySelector(".x").onclick = () => history.back();
  const part = g.querySelector(".gpart"); if (part) part.onclick = () => NATIVE.openAppSettings();
  const paintSel = () => {
    grid.querySelectorAll(".gt").forEach(t => { const k = picked.findIndex(p => p.key === t.dataset.key); t.classList.toggle("sel", k >= 0); t.querySelector(".n").textContent = k >= 0 ? k + 1 : ""; });
    bar.hidden = !picked.length; bar.querySelector("span").textContent = `${picked.length} selected`;
  };
  const tileCam = () => { const t = document.createElement("button"); t.className = "gt gcam"; t.innerHTML = `${CI.camera}<span>Camera</span>`; t.onclick = () => { galClose(); history.back(); setTimeout(() => chatCamera(el), 80); }; grid.appendChild(t); };
  const more = () => {
    if (loading || done) return; loading = true;
    let page = []; try { page = JSON.parse(NATIVE.galleryPage(offset, 60, kind)); } catch(e){}
    offset += page.length; if (page.length < 60) done = true;
    page.forEach(m => {
      const key = m.type + "/" + m.id, t = document.createElement("button"); t.className = "gt"; t.dataset.key = key;
      t.innerHTML = `<img alt="" loading="lazy" decoding="async" src="/__local/thumb/${key}">${m.type === "video" ? `<span class="vd">▶ ${fmtSec(Math.round(m.dur || 0))}</span>` : ""}<i class="n"></i>`;
      t.onclick = () => { const k = picked.findIndex(p => p.key === key); if (k >= 0) picked.splice(k, 1); else if (picked.length < 30) picked.push({key, ...m}); else toast("Up to 30 at a time."); paintSel(); };
      grid.appendChild(t);
    });
    if (!offset && done) grid.insertAdjacentHTML("beforeend", `<p class="gempty">No photos or videos found on this phone.</p>`);
    loading = false; paintSel();
  };
  const reset = () => { grid.innerHTML = ""; offset = 0; done = false; tileCam(); more(); };
  g.querySelectorAll(".seg2 button").forEach(b => b.onclick = () => { kind = b.dataset.k; g.querySelectorAll(".seg2 button").forEach(x => x.classList.toggle("on", x === b)); reset(); });
  grid.onscroll = () => { if (grid.scrollTop + grid.clientHeight > grid.scrollHeight - 600) more(); };
  bar.querySelector("button").onclick = async () => {
    const btn = bar.querySelector("button"); btn.disabled = true; btn.textContent = "Loading…";
    const files = [];
    for (const p of picked) {
      try { const r = await fetch(`/__local/file/${p.key}`); const b = await r.blob(); files.push(new File([b], `${p.type === "video" ? "video" : "photo"}-${p.id}.${(p.mime || b.type || "").split("/")[1] || "jpg"}`, {type: p.mime || b.type})); }
      catch(e) { toast("Couldn't open one of those."); }
    }
    galClose(); history.back();
    if (files.length) setTimeout(() => openEditor(el, files), 80);
  };
  reset();
}
function galBack(){ if (history.state && history.state.cgal) return; galClose(); }
function galClose(){ window.removeEventListener("popstate", galBack); const g = $("cgal"); if (g) g.remove(); }
/** The phone's own picker (website, or when gallery access is refused). */
function pickFiles(el){''')
rep("</style>\n</head>", r""".cgal{position:absolute;inset:0;z-index:8;background:#08090C;display:grid;grid-template-rows:auto auto minmax(0,1fr) auto}
.cgal .gh{display:grid;grid-template-columns:auto auto 1fr;gap:12px;align-items:center;padding:calc(env(safe-area-inset-top,0px) + 10px) 12px 10px;border-bottom:1px solid var(--line)}
.cgal .gh .x{width:40px;height:40px;border-radius:50%;border:0;background:none;color:var(--ink);font-size:20px;cursor:pointer}
.cgal .gh b{font-family:var(--f-display);font-weight:800;letter-spacing:.08em;text-transform:uppercase;font-size:19px}
.cgal .seg2{justify-self:end;display:flex;background:#14161c;border-radius:999px;padding:3px;gap:2px}
.cgal .seg2 button{border:0;background:none;color:var(--muted);border-radius:999px;padding:6px 11px;font:inherit;font-size:12.5px;font-weight:600;cursor:pointer}
.cgal .seg2 button.on{background:#7C8BFF;color:#0A0C16}
.cgal .gpart{border:0;background:#141a3a;color:var(--ink);padding:10px 14px;font:inherit;font-size:13px;text-align:left;cursor:pointer}
.cgal .gg{overflow-y:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:3px;padding:3px;align-content:start}
.cgal .gt{position:relative;aspect-ratio:1;border:0;padding:0;background:#14161c;overflow:hidden;cursor:pointer}
.cgal .gt img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .15s}
.cgal .gt.sel img{transform:scale(.86);border-radius:8px}
.cgal .gt .n{position:absolute;top:6px;right:6px;width:24px;height:24px;border-radius:50%;border:2px solid #fff;background:rgba(0,0,0,.25);font-style:normal;font-family:var(--f-mono);font-size:12px;font-weight:700;display:grid;place-content:center;color:#0A0C16}
.cgal .gt.sel .n{background:#7C8BFF;border-color:#7C8BFF}
.cgal .gt .vd{position:absolute;left:6px;bottom:6px;font-family:var(--f-mono);font-size:11px;color:#fff;text-shadow:0 1px 4px #000}
.cgal .gcam{display:grid;place-content:center;justify-items:center;gap:6px;color:var(--accent);background:#10131d}
.cgal .gcam svg{width:30px;height:30px}.cgal .gcam span{font-size:12px;font-weight:600;color:var(--ink)}
.cgal .gempty{grid-column:1 / -1;text-align:center;color:var(--muted);padding:30px}
.cgal .gbar{display:flex;justify-content:space-between;align-items:center;padding:10px 14px calc(env(safe-area-inset-bottom,0px) + 10px);background:#111318;border-top:1px solid var(--line)}
.cgal .gbar[hidden]{display:none}
</style>
</head>""")
open(P, "w", encoding="utf-8", newline="\n").write(s)

SW = os.path.join(ROOT, "sw.js"); w = open(SW, encoding="utf-8").read()
a = '''  if (same && url.pathname.startsWith("/api/media/")) {'''
assert a in w
w = w.replace(a, '''  if (same && url.pathname.startsWith("/__local/")) return;           // the app's own gallery: answered by the app, never cached
''' + a)
open(SW, "w", encoding="utf-8", newline="\n").write(w)
print("ok")
