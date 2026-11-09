"""Adds the 75-day challenge board (rules strip with icons + day-by-day grid) and the crew activity feed."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..", "index.html")
s = open(P, encoding="utf-8").read()
assert "function openBoard" not in s, "already patched"

def rep(old, new, count=1):
    global s
    n = s.count(old); assert n >= count, (n, old[:100]); s = s.replace(old, new, count)

CSS = r'''
/* ---------- challenge board ---------- */
.rules{display:grid;grid-template-columns:repeat(auto-fit,minmax(86px,1fr));gap:8px}
.rule-i{display:grid;justify-items:center;gap:6px;text-align:center;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:12px 6px}
.rule-i svg{width:30px;height:30px;color:var(--ink)}
.rule-i span{font-size:11.5px;line-height:1.25;color:var(--muted)}
.board{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.bcol{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:10px 12px}
.brow{display:grid;align-items:center;gap:4px;padding:3px 0;border-radius:8px;cursor:pointer}
.brow:hover{background:var(--sunk)}
.brow .bn{font-family:var(--f-display);font-weight:800;font-size:15px;text-align:right;padding-right:6px;color:var(--muted)}
.brow.today{background:var(--brass-soft)}
.brow.today .bn{color:var(--brass)}
.brow.failed .bn{color:var(--warn)}
.bh{display:grid;align-items:center;gap:4px;padding:0 0 6px;border-bottom:1px solid var(--line);margin-bottom:4px}
.bh svg{width:15px;height:15px;justify-self:center;color:var(--muted)}
.bc{width:20px;height:20px;justify-self:center;border:1.5px solid var(--line-strong);border-radius:5px;display:grid;place-content:center}
.bc.on{background:var(--accent);border-color:var(--accent)}
.bc.on::after{content:"";width:9px;height:5px;border-left:2px solid var(--accent-ink);border-bottom:2px solid var(--accent-ink);transform:rotate(-45deg) translate(1px,-1px)}
.bc.miss{border-color:var(--warn);background:var(--warn-soft)}
.bc.future{opacity:.45}
.goal .gic{width:28px;height:28px;display:grid;place-content:center;color:var(--muted)}
.goal .gic svg{width:22px;height:22px}
/* ---------- crew feed + toasts ---------- */
.feed{display:grid;gap:2px;border-top:1px solid var(--line);padding-top:10px}
.feed .fl{margin-bottom:4px}
.fev{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;font-size:13.5px;padding:5px 0}
.fev b{font-weight:600}
.fev time{font-family:var(--f-mono);font-size:11px;color:var(--muted);white-space:nowrap}
.toasts{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 16px);z-index:70;display:grid;gap:8px;width:min(92vw,420px)}
.toast{background:var(--ink);color:var(--bg);border-radius:16px;padding:12px 16px;font-size:14px;box-shadow:0 12px 32px rgba(0,0,0,.35);display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:center;animation:tin .25s ease-out}
.toast .tdot{width:10px;height:10px;border-radius:50%;background:var(--accent)}
@keyframes tin{from{transform:translateY(10px);opacity:0}to{transform:none;opacity:1}}
'''
rep("</style>", CSS + "</style>", 1)

JS = r'''
/* =========================================================== challenge board + icons */
const ICONS = {
  tree: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"><path d="M12 22v-6"/><path d="M8 16h8a4 4 0 0 0 1.2-7.8A5.5 5.5 0 0 0 6.6 8.4 4 4 0 0 0 8 16z"/><path d="M12 16l-2.5-2.5M12 18l2.5-2.5"/></svg>',
  dumbbell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M6.5 6.5l11 11"/><path d="M4 9.5 9.5 4M14.5 20 20 14.5"/><path d="M2.5 11 11 2.5M13 21.5 21.5 13"/></svg>',
  plate: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 3v4M12 17v4"/></svg>',
  glass: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M6 3h12l-1.6 17.2a2 2 0 0 1-2 1.8H9.6a2 2 0 0 1-2-1.8z"/><path d="M6.6 10h10.8"/></svg>',
  nobottle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3h4v4l2 3v10a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V10l2-3z"/><circle cx="12" cy="13" r="9.5"/><path d="M5.5 6.5l13 13"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M12 6c-2-1.5-5-2-8-1.5v14c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5v-14c-3-.5-6 0-8 1.5z"/><path d="M12 6v14"/></svg>',
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><path d="M3 8h4l2-3h6l2 3h4v12H3z"/><circle cx="12" cy="13.5" r="3.8"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16 10"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  count: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M5 9h14M5 15h14M10 4l-2 16M16 4l-2 16"/></svg>',
};
const iconFor = g => ICONS[g.icon] || (g.type === "time" ? ICONS.clock : g.type === "count" ? ICONS.count : ICONS.check);
function openBoard(){
  const cs = challengeState(keyOf(new Date())), G = goalsList(), today = keyOf(new Date());
  if (!cs) return;
  const o = openOverlay();
  o.innerHTML = `<div class="in" style="max-width:1100px"><div class="bar"><span class="prog">${cs.name} · Day ${cs.dayN} of ${cs.length}</span><button class="close">✕ Close</button></div>
    <h2 class="exname" style="font-size:44px">${cs.name.toUpperCase()} CHALLENGE</h2>
    <div class="rgtitle">The rules</div><div class="rules"></div>
    <p class="beat">${cs.strict ? "Every rule, every day. Miss one and you start again at Day 1." : "Do every rule each day. A missed day doesn't reset you."} Tap a day to open it.</p>
    <div class="board"></div></div>`;
  o.querySelector(".close").onclick = () => closeOverlay();
  const rules = o.querySelector(".rules");
  G.forEach(g => { const r = document.createElement("div"); r.className = "rule-i"; r.innerHTML = iconFor(g) + "<span></span>"; r.querySelector("span").textContent = g.name; rules.appendChild(r); });
  const cols = `34px repeat(${G.length}, minmax(0,1fr))`;
  const board = o.querySelector(".board");
  const per = Math.ceil(cs.length / 3);
  for (let c = 0; c < 3; c++) {
    const col = document.createElement("div"); col.className = "bcol";
    const head = document.createElement("div"); head.className = "bh"; head.style.gridTemplateColumns = cols;
    head.innerHTML = "<span></span>" + G.map(g => iconFor(g)).join("");
    col.appendChild(head);
    for (let i = c * per; i < Math.min(cs.length, (c + 1) * per); i++) {
      const k = shift(cs.start, i), gv = getDay(k).goals || {}, past = k < today, full = goalProgress(k).frac >= 1;
      const row = document.createElement("div"); row.className = "brow" + (k === today ? " today" : "") + (past && !full ? " failed" : "");
      row.style.gridTemplateColumns = cols;
      row.innerHTML = `<span class="bn">${i + 1}.</span>` + G.map(g => {
        const ok = goalDone(g, gv[g.id]);
        return `<span class="bc${ok ? " on" : past ? " miss" : k > today ? " future" : ""}"></span>`;
      }).join("");
      row.title = fromKey(k).toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short"});
      if (k <= today) row.onclick = () => { sel = k; closeOverlay(); render(); };
      col.appendChild(row);
    }
    board.appendChild(col);
  }
}

/* =========================================================== crew activity: events, feed, in-app alerts */
const feedState = {events: [], unsub: null, code: null, seen: new Set(), since: Date.now()};
function crewEvent(text){
  const fs = crewFS(), crews = settings.crews || []; if (!fs || !crews.length) return;
  const name = (profile().name || fs.user.displayName || "Someone").split(" ")[0];
  const ev = {uid: fs.uid, name, text, ts: Date.now(), at: firebase.firestore.FieldValue.serverTimestamp()};
  crews.forEach(code => fs.db.collection("groups").doc(code).collection("events").add(ev).catch(() => {}));
  if (window.__ordoNotifyCrew) window.__ordoNotifyCrew(name, text);
}
function watchFeed(){
  const fs = crewFS(), code = (settings.crews || [])[0] || null;
  if (feedState.code === code && feedState.unsub) return;
  if (feedState.unsub) { feedState.unsub(); feedState.unsub = null; }
  feedState.code = code; feedState.events = [];
  if (!fs || !code) return;
  feedState.unsub = fs.db.collection("groups").doc(code).collection("events").orderBy("ts", "desc").limit(20).onSnapshot(snap => {
    feedState.events = snap.docs.map(d => ({id: d.id, ...d.data()}));
    snap.docChanges().forEach(ch => {
      const e = ch.doc.data();
      if (ch.type === "added" && e.uid !== fs.uid && e.ts > feedState.since && !feedState.seen.has(ch.doc.id)) {
        feedState.seen.add(ch.doc.id);
        alertCrew(`${e.name} ${e.text}`);
      }
    });
    renderCrew();
  }, () => {});
}
function toast(msg){
  let t = document.querySelector(".toasts"); if (!t) { t = document.createElement("div"); t.className = "toasts"; document.body.appendChild(t); }
  const e = document.createElement("div"); e.className = "toast"; e.innerHTML = `<span class="tdot"></span><span></span>`; e.lastChild.textContent = msg;
  t.appendChild(e); setTimeout(() => e.remove(), 5000);
}
function alertCrew(msg){
  toast(msg);
  try {
    if (NATIVE && NATIVE.notify) NATIVE.notify("Your crew", msg);
    else if (document.hidden && "Notification" in window && Notification.permission === "granted") new Notification("Your crew · ORDO", {body: msg, icon: "icon-192.png"});
  } catch(e){}
}
const ago = ts => { const s = Math.max(0, (Date.now() - ts) / 1000); return s < 60 ? "now" : s < 3600 ? Math.floor(s / 60) + "m" : s < 86400 ? Math.floor(s / 3600) + "h" : Math.floor(s / 86400) + "d"; };
'''
rep('''/* =========================================================== onboarding + settings */''', JS + '''
/* =========================================================== onboarding + settings */''')

# goal rows: icon instead of the plain checkbox column for counts; check goals keep the box
rep('''      row.innerHTML = `<input type="checkbox" class="chk" id="goal-${i}" tabindex="-1"><label class="gname" for="goal-${i}"></label>''',
    '''      row.innerHTML = `<span class="gic">${iconFor(g)}</span><label class="gname"></label>''')
rep('''      row.querySelector("input").checked = done;
      row.querySelector("input").onchange = e => setGoal(g.id, e.target.checked ? t : null);
      row.querySelector(".gval")''', '''      row.querySelector(".gval")''')
# board link under the challenge header
rep('''    tr.style.gridTemplateColumns = `repeat(${cs.length},minmax(0,1fr))`;
    box.appendChild(ch);''', '''    tr.style.gridTemplateColumns = `repeat(${cs.length},minmax(0,1fr))`;
    const bl = document.createElement("button"); bl.className = "linkbtn"; bl.style.gridColumn = "1 / -1"; bl.textContent = `Open the ${cs.length}-day board`;
    bl.onclick = openBoard; ch.appendChild(bl);
    box.appendChild(ch);''')

# goal completion -> crew event (only when it flips to done today)
rep('''function setGoal(id, v){
  const d = ensure(sel); d.goals = {...(d.goals || {})};''', '''function setGoal(id, v){
  const d = ensure(sel), g = goalsList().find(x => x.id === id), wasDone = g && goalDone(g, (d.goals || {})[id]), wasAll = goalProgress(sel).frac >= 1;
  d.goals = {...(d.goals || {})};''')
rep('''  if (v === null || v === false || v === 0) delete d.goals[id]; else d.goals[id] = v;
  saveDay(d, false); render();''', '''  if (v === null || v === false || v === 0) delete d.goals[id]; else d.goals[id] = v;
  saveDay(d, false);
  if (sel === keyOf(new Date()) && g && !wasDone && goalDone(g, d.goals[id])) {
    const cs = challengeState(sel);
    if (!wasAll && goalProgress(sel).frac >= 1) crewEvent(cs ? `completed Day ${cs.dayN} of ${cs.name}. Every rule done.` : "finished every goal today.");
    else crewEvent(`finished “${g.name}”${cs ? ` · Day ${cs.dayN}` : ""}.`);
  }
  render();''')
# workouts finished from a goal also count
rep('''  const {ids, mins, d} = saveWorkoutLog();''', '''  const {ids, mins, d} = saveWorkoutLog();
  if (ids.length) crewEvent(`finished a guided workout: ${ids.length} exercises, ${mins} min.`);''')

# feed inside the crew panel
rep('''  const f = document.createElement("div"); f.className = "redfoot";
  const inv = document.createElement("a");''', '''  if (feedState.events.length) {
    const feed = document.createElement("div"); feed.className = "feed";
    feed.innerHTML = `<div class="fl">Live</div>`;
    feedState.events.slice(0, 8).forEach(e => {
      const r = document.createElement("div"); r.className = "fev"; r.innerHTML = `<span><b></b> <span></span></span><time></time>`;
      r.querySelector("b").textContent = e.uid === fs.uid ? "You" : e.name; r.querySelector("span span").textContent = e.text; r.querySelector("time").textContent = ago(e.ts);
      feed.appendChild(r);
    });
    box.appendChild(feed);
  }
  const f = document.createElement("div"); f.className = "redfoot";
  const inv = document.createElement("a");''')
rep('''      watchCrew(); renderCrew();''', '''      watchCrew(); watchFeed(); renderCrew();''')
rep('''  settings.crews = [code, ...(settings.crews || [])]; saveSettings(); crewState.last = ""; pushCrew(); watchCrew(); renderCrew();''',
    '''  settings.crews = [code, ...(settings.crews || [])]; saveSettings(); crewState.last = ""; pushCrew(); watchCrew(); watchFeed(); renderCrew();''')
rep('''  crewState.last = ""; pushCrew(); watchCrew(); renderCrew();
  return "";''', '''  crewState.last = ""; pushCrew(); watchCrew(); watchFeed(); renderCrew();
  crewEvent("joined the crew.");
  return "";''')

open(P, "w", encoding="utf-8", newline="\n").write(s)
print("board + feed applied")
