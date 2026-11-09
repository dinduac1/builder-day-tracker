"""One-off: hosted programs set by admins (Firestore programs/*), member profiles with photo,
ORDO-branded sign-in screen, and a trimmed goal library."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()

def rep(a, b):
    global s
    assert s.count(a) == 1, f"{s.count(a)} matches: " + a[:90]
    s = s.replace(a, b)

# ---- library: only what fits ORDO
rep('''  {id:"diet", icon:"plate", short:"Diet", name:"Follow your diet. No cheat meals", type:"check"},
  {id:"alcohol", icon:"nobottle", short:"No alcohol", name:"No alcohol", type:"check"},
''', "")

# ---- CSS
rep("</style>\n</head>", r""".obphoto{width:112px;height:112px;border-radius:50%;border:1.5px dashed var(--line-strong);background:var(--surface);display:grid;place-content:center;cursor:pointer;overflow:hidden;justify-self:center;color:var(--muted);font-size:13px;text-align:center;padding:0}
.obphoto img{width:100%;height:100%;object-fit:cover;display:block}
.obform{display:grid;gap:10px}
.obform .tx{font-size:17px;padding:13px 15px}
.hostnote{grid-column:1 / -1;font-family:var(--f-mono);font-size:11px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
.admrow{display:grid;grid-template-columns:minmax(0,1fr) 104px 72px 64px 34px;gap:6px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}
.admrow .an,.admrow .ao{grid-column:1 / -1}
.admrow input,.admrow select{font:inherit;font-size:13.5px;padding:8px 9px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);min-width:0;width:100%}
.admrow .an{font-weight:600;font-size:15px}
.admrow .x{height:34px;border-radius:9px;border:1px solid var(--line);background:var(--bg);cursor:pointer;color:var(--warn)}
.admrow .lk{grid-column:1 / -1;font-family:var(--f-mono);font-size:11px;color:var(--accent)}
.member .ms .city{color:var(--ink)}
</style>
</head>""")

# ---- goals come from the hosts' program when you're on one
rep("const goalsList = () => settings.goals || [];",
    "const goalsList = () => { const h = hostedProgram(); return h && Array.isArray(h.goals) ? h.goals : (settings.goals || []); };")
rep("function applyProgram(key, startToday){\n  const P = PROGRAMS[key];", "function applyProgram(key, startToday){\n  const P = programDef(key);")

# goals panel: hosted rules can't be edited by members
rep('''  const foot = document.createElement("div"); foot.className = "redfoot"; foot.style.paddingTop = "12px";
  const ed = document.createElement("button"); ed.className = "linkbtn"; ed.textContent = "Edit goals";
  ed.onclick = () => { goalDraft = goalsList().map(g => ({...g})); editingGoals = true; render(); };
  foot.appendChild(ed);''', '''  const foot = document.createElement("div"); foot.className = "redfoot"; foot.style.paddingTop = "12px";
  if (hostedProgram()) {
    const hn = document.createElement("span"); hn.className = "hostnote"; hn.textContent = "Rules set by the hosts. Same for everyone.";
    foot.appendChild(hn);
    if (isAdmin()) { const ae = document.createElement("button"); ae.className = "linkbtn"; ae.textContent = "Edit these rules (admin)"; ae.onclick = () => openAdmin(profile().program); foot.appendChild(ae); }
  } else {
    const ed = document.createElement("button"); ed.className = "linkbtn"; ed.textContent = "Edit goals";
    ed.onclick = () => { goalDraft = goalsList().map(g => ({...g})); editingGoals = true; render(); };
    foot.appendChild(ed);
  }''')

# program pickers list hosted programs
rep('''    ["75hard", "custom"].forEach(k => {
      const P = PROGRAMS[k], c = document.createElement("button"); c.className = "prog-card";''', '''    programKeys(false).forEach(k => {
      const P = programDef(k), c = document.createElement("button"); c.className = "prog-card";''')
rep('''    ["75hard", "builder", "custom"].forEach(k => {
      const P = PROGRAMS[k], c = document.createElement("button"); c.className = "prog-card";''', '''    programKeys(true).forEach(k => {
      const P = programDef(k), c = document.createElement("button"); c.className = "prog-card";''')
rep('''  ["75hard", "custom"].forEach(k => {
    const P = PROGRAMS[k], card = document.createElement("button"); card.className = "prog-card" + (p.program === k ? " on" : "");''', '''  programKeys(false).forEach(k => {
    const P = programDef(k), card = document.createElement("button"); card.className = "prog-card" + (p.program === k ? " on" : "");''')

# ---- crew rows carry the profile
rep('''  return {name: (profile().name || (me && me.user.displayName) || "Member").slice(0, 40), photo: (me && me.user.photoURL) || "",''',
    '''  return {name: (profile().name || (me && me.user.displayName) || "Member").slice(0, 40), photo: profile().photo || (me && me.user.photoURL) || "",
    city: (profile().city || "").slice(0, 40), headline: (profile().headline || "").slice(0, 80),''')
rep('''    row.querySelector(".ms").textContent = fresh ? `Today ${m.today.done}/${m.today.total}${m.grade ? " · " + m.grade : ""}` : "Not updated today";''',
    '''    row.querySelector(".ms").textContent = (m.city ? m.city + " · " : "") + (fresh ? `Today ${m.today.done}/${m.today.total}${m.grade ? " · " + m.grade : ""}` : "Not updated today");
    if (m.headline) row.querySelector(".mn").title = m.headline;''')

# ---- onboarding: profile step replaces the name step
rep('''  } else if (step === "name") {
    const me = crewFS();
    b.innerHTML = `<h2>What should we call you?</h2><input class="tx" id="obName" maxlength="40" placeholder="First name" style="font-size:20px;padding:14px 16px"><button class="btn primary block" id="obNext">Continue</button>`;
    b.querySelector("#obName").value = profile().name || (me && me.user.displayName ? me.user.displayName.split(" ")[0] : "");
    b.querySelector("#obNext").onclick = () => { settings.profile = {...profile(), name: b.querySelector("#obName").value.trim()}; saveSettings(); onboarding("program"); };''',
'''  } else if (step === "name" || step === "profile") {
    b.innerHTML = `<h2>Your profile.</h2><p class="lead">This is how your crew and the leaderboard see you.</p><div class="pf"></div>`;
    profileForm(b.querySelector(".pf"), "Continue", () => onboarding("program"));''')
rep('''    <div class="setgrp"><h3>You</h3><label class="fl" for="stName">Name</label><input class="tx" id="stName" maxlength="40">
      <div class="beat" id="stWho"></div></div>''', '''    <div class="setgrp"><h3>You</h3><div id="stProfile"></div><div class="beat" id="stWho"></div></div>
    <div class="setgrp" id="stAdminGrp" hidden><h3>Admin</h3><p class="beat">You host programs. What you set here is what every member on that program tracks.</p>
      <div class="redfoot"><button class="btn-sm" id="stAdmin">Programs &amp; admins</button></div></div>''')
rep('''  const nm = o.querySelector("#stName"); nm.value = p.name || "";
  nm.onchange = () => { settings.profile = {...profile(), name: nm.value.trim()}; saveSettings(); };''',
'''  profileForm(o.querySelector("#stProfile"), "Save profile", () => toast("Profile saved."));
  if (isAdmin()) { o.querySelector("#stAdminGrp").hidden = false; o.querySelector("#stAdmin").onclick = () => openAdmin(); }''')

# ---- branded sign-in: signed out, the ORDO screen leads (unless they chose to stay local this session)
rep('''      if (!Object.keys(days).length && !settings.profile && !sessionStorage.getItem("ordo-local")) onboarding("welcome");''',
    '''      if (!sessionStorage.getItem("ordo-local")) onboarding("welcome");''')
rep('''        else setTimeout(() => onboarding("name"), 50);''', '''        else setTimeout(() => onboarding("profile"), 50);''')
rep('''      watchCrew(); watchFeed(); renderCrew(); registerCrewDevice();''', '''      watchCrew(); watchFeed(); renderCrew(); registerCrewDevice(); watchHosted();''')
rep('''    if (crewState.unsub) { crewState.unsub(); crewState.unsub = null; crewState.code = null; }''',
    '''    if (crewState.unsub) { crewState.unsub(); crewState.unsub = null; crewState.code = null; }
    unwatchHosted();''')
rep('''<button class="btn primary block" id="obSign"><span>Sign in with Google</span></button>''',
    '''<button class="btn primary block" id="obSign">${G_ICON_SM}<span>Continue with Google</span></button>''')

# ---- the new code
rep("/* ---------- boot ---------- */\n$(\"brandMark\").innerHTML = BRAND_SVG;", r'''/* =========================================================== profile */
const G_ICON_SM = '<svg viewBox="0 0 48 48" width="18" height="18" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>';
/** Shrink a chosen photo to a 256px square JPEG (about 20 KB), so it can live in the profile itself. */
function squarePhoto(file){
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => {
      const S = 256, c = document.createElement("canvas"); c.width = c.height = S;
      const k = Math.max(S / img.width, S / img.height), w = img.width * k, h = img.height * k;
      c.getContext("2d").drawImage(img, (S - w) / 2, (S - h) / 2, w, h);
      URL.revokeObjectURL(img.src); res(c.toDataURL("image/jpeg", .82));
    };
    img.onerror = () => rej(new Error("That file isn't a photo we can read."));
    img.src = URL.createObjectURL(file);
  });
}
function profileForm(box, label, done){
  const p = profile(), me = crewFS();
  let photo = p.photo || (me && me.user.photoURL) || "";
  box.innerHTML = `<div class="obform"><button class="obphoto" type="button" aria-label="Choose a profile photo"></button><input type="file" accept="image/*" hidden>
    <label class="fl" for="pfName">Name</label><input class="tx" id="pfName" maxlength="40" placeholder="First name" autocomplete="given-name">
    <label class="fl" for="pfCity">City</label><input class="tx" id="pfCity" maxlength="40" placeholder="e.g. Enugu" autocomplete="address-level2">
    <label class="fl" for="pfHead">What are you building?</label><input class="tx" id="pfHead" maxlength="80" placeholder="e.g. A design agency, a stronger body">
    <button class="btn primary block" id="pfSave"></button><p class="beat" id="pfMsg"></p></div>`;
  const pb = box.querySelector(".obphoto"), file = box.querySelector("input[type=file]");
  const showPhoto = () => { pb.innerHTML = photo ? `<img alt="" referrerpolicy="no-referrer">` : "Add a<br>photo"; if (photo) pb.querySelector("img").src = photo; };
  showPhoto();
  pb.onclick = () => file.click();
  file.onchange = async () => { const f = file.files && file.files[0]; if (!f) return; try { photo = await squarePhoto(f); showPhoto(); } catch(e) { box.querySelector("#pfMsg").textContent = e.message; } };
  const nm = box.querySelector("#pfName"), ct = box.querySelector("#pfCity"), hd = box.querySelector("#pfHead");
  nm.value = p.name || (me && me.user.displayName ? me.user.displayName.split(" ")[0] : ""); ct.value = p.city || ""; hd.value = p.headline || "";
  const sv = box.querySelector("#pfSave"); sv.textContent = label;
  sv.onclick = () => {
    if (!nm.value.trim()) { box.querySelector("#pfMsg").textContent = "Add your name so your crew knows who you are."; nm.focus(); return; }
    settings.profile = {...profile(), name: nm.value.trim(), city: ct.value.trim(), headline: hd.value.trim(), photo};
    saveSettings(); crewState.last = ""; pushCrew(); done && done();
  };
}

/* =========================================================== hosted programs (admins) */
// Founders are always admins; they can add co-hosts in Settings → Admin. firestore.rules holds the same list.
const FOUNDERS = ["dinduking1@gmail.com", "chimdindu@empirewords.com"];
const hosted = {programs: {}, admins: [], unsub: null, unsubA: null};
const myEmail = () => { const fs = crewFS(); return fs && fs.user.email ? fs.user.email.toLowerCase() : ""; };
const isAdmin = () => !!myEmail() && (FOUNDERS.includes(myEmail()) || hosted.admins.includes(myEmail()));
const hostedProgram = () => { const k = (settings.profile || {}).program; return k && hosted.programs[k] && hosted.programs[k].goals ? hosted.programs[k] : null; };
const programDef = k => hosted.programs[k] ? {...(PROGRAMS[k] || {}), ...hosted.programs[k], challenge: {name: hosted.programs[k].name, length: hosted.programs[k].length || 75, strict: hosted.programs[k].strict !== false}} : PROGRAMS[k];
const programKeys = withBuilder => [...new Set(["75hard", ...Object.keys(hosted.programs).filter(k => !hosted.programs[k].hidden)])].concat(withBuilder ? ["builder", "custom"] : ["custom"]);
function watchHosted(){
  const fs = crewFS(); if (!fs || hosted.unsub) return;
  hosted.unsub = fs.db.collection("programs").onSnapshot(snap => {
    hosted.programs = Object.fromEntries(snap.docs.map(d => [d.id, d.data()]));
    syncHostedChallenge(); render();
  }, () => {});
  hosted.unsubA = fs.db.collection("config").doc("admins").onSnapshot(d => {
    hosted.admins = ((d.exists && d.data().emails) || []).map(e => String(e).toLowerCase()); render();
  }, () => {});
}
function unwatchHosted(){ if (hosted.unsub) hosted.unsub(); if (hosted.unsubA) hosted.unsubA(); hosted.unsub = hosted.unsubA = null; hosted.programs = {}; hosted.admins = []; }
/** Keep my copy of a hosted program (name, length, rules) in step with what the hosts publish. */
function syncHostedChallenge(){
  const h = hostedProgram(); if (!h) return;
  const c = settings.challenge || {}, want = {name: h.name, length: h.length || 75, strict: h.strict !== false};
  const goalsSig = JSON.stringify(h.goals), changed = c.name !== want.name || c.length !== want.length || c.strict !== want.strict || JSON.stringify(settings.goals) !== goalsSig;
  if (!changed) return;
  settings.challenge = {...c, ...want, start: c.start || keyOf(new Date())};
  settings.goals = h.goals.map(g => ({...g}));   // offline copy
  saveSettings();
}
const slug = t => String(t || "").toLowerCase().replace(/[^a-z0-9]+/g, "").slice(0, 24) || "p" + Date.now().toString(36);
let admDraft = null;
function openAdmin(editKey){
  if (!isAdmin()) return;
  openOverlay();
  if (editKey) return drawProgramEditor(editKey);
  drawAdmin();
}
function drawAdmin(){
  const o = ovl(), fs = crewFS();
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">Admin</span><button class="close">✕ Close</button></div>
    <h2 class="exname">Programs</h2><p class="beat">Programs you publish appear for every member when they pick a program. Members on a program track exactly your rules; change them here and everyone updates.</p>
    <div class="progs" id="admList"></div><button class="btn block" id="admNew">+ Create a program</button>
    <div class="rgtitle">Admins</div><div id="admAdmins"></div></div>`;
  o.querySelector(".close").onclick = () => { closeOverlay(); render(); };
  const list = o.querySelector("#admList");
  const keys = [...new Set(["75hard", ...Object.keys(hosted.programs)])];
  keys.forEach(k => {
    const h = hosted.programs[k], P = programDef(k), c = document.createElement("div"); c.className = "wcard";
    c.innerHTML = `<b></b><span></span><div class="acts"><button class="linkbtn">Edit</button></div>`;
    c.querySelector("b").textContent = P.name;
    c.querySelector("span").textContent = h ? `${(h.goals || []).length} rules · ${h.length || 75} days · ${h.strict !== false ? "strict" : "forgiving"}${h.hidden ? " · hidden" : " · live"}` : "Built-in default. Edit it to publish your own version.";
    c.querySelector("button").onclick = () => drawProgramEditor(k);
    list.appendChild(c);
  });
  o.querySelector("#admNew").onclick = () => drawProgramEditor(null);
  const ab = o.querySelector("#admAdmins");
  const all = [...FOUNDERS.map(e => [e, true]), ...hosted.admins.filter(e => !FOUNDERS.includes(e)).map(e => [e, false])];
  all.forEach(([e, founder]) => {
    const r = document.createElement("div"); r.className = "fev"; r.innerHTML = `<span></span><span></span>`;
    r.firstChild.textContent = e;
    if (founder) r.lastChild.textContent = "founder";
    else { const x = document.createElement("button"); x.className = "linkbtn"; x.style.color = "var(--warn)"; x.textContent = "Remove"; x.onclick = () => saveAdmins(hosted.admins.filter(a => a !== e)); r.lastChild.appendChild(x); }
    ab.appendChild(r);
  });
  const add = document.createElement("div"); add.className = "crewjoin";
  add.innerHTML = `<input class="tx ed" type="email" placeholder="Co-host's Google email" autocomplete="off"><button class="btn">Add</button>`;
  add.querySelector("button").onclick = () => { const e = add.querySelector("input").value.trim().toLowerCase(); if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) saveAdmins([...new Set([...hosted.admins, e])]); else toast("Enter their Google email."); };
  ab.appendChild(add);
  function saveAdmins(emails){
    fs.db.collection("config").doc("admins").set({emails, updated: firebase.firestore.FieldValue.serverTimestamp()})
      .then(() => { hosted.admins = emails; drawAdmin(); toast("Admins updated."); }).catch(e => toast("Couldn't save: " + e.message));
  }
}
function drawProgramEditor(key){
  const P = key ? programDef(key) : null;
  if (!admDraft || admDraft.key !== key) admDraft = {key, name: P ? P.name : "", sub: P ? P.sub || "" : "", length: P ? (P.length || (P.challenge || {}).length || 75) : 75,
    strict: P ? (P.strict !== undefined ? P.strict !== false : !!(P.challenge || {}).strict) : true, hidden: P ? !!P.hidden : false, goals: P ? (P.goals || []).map(g => ({...g})) : []};
  const D = admDraft, o = ovl();
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">${key ? "Edit program" : "New program"}</span><button class="close">← Back</button></div>
    <input class="wname" id="apName" maxlength="40" placeholder="Program name, e.g. 75 Hard">
    <label class="fl" for="apSub">What it is (members see this when they choose)</label><input class="tx" id="apSub" maxlength="240">
    <div class="setgrp"><label class="toggle"><span>Strict: a missed rule sends them back to Day 1</span><input type="checkbox" id="apStrict"></label>
      <label class="toggle"><span>Hidden from members (draft)</span><input type="checkbox" id="apHidden"></label>
      <label class="fl" for="apLen">Length in days</label><input class="tx" id="apLen" type="number" min="1" max="365" inputmode="numeric" style="max-width:120px"></div>
    <div class="rgtitle">Daily rules · ${D.goals.length}</div><div id="apRules"></div>
    <button class="btn block" id="apAdd">+ Write a rule</button>
    <div class="libcat"><h4>Quick add</h4><div class="chips2" id="apLib"></div></div>
    <div class="savebar"><button class="btn primary" id="apSave">Publish</button><button class="btn" id="apCancel">Cancel</button></div></div>`;
  const back = () => { admDraft = null; drawAdmin(); };
  o.querySelector(".close").onclick = o.querySelector("#apCancel").onclick = back;
  const f = (id, prop, num) => { const e = o.querySelector(id); e.value = D[prop]; e.oninput = () => { D[prop] = num ? Number(e.value) || 0 : e.value; }; };
  f("#apName", "name"); f("#apSub", "sub"); f("#apLen", "length", true);
  const st = o.querySelector("#apStrict"); st.checked = D.strict; st.onchange = () => { D.strict = st.checked; };
  const hd = o.querySelector("#apHidden"); hd.checked = D.hidden; hd.onchange = () => { D.hidden = hd.checked; };
  const rules = o.querySelector("#apRules");
  D.goals.forEach((g, i) => {
    const r = document.createElement("div"); r.className = "admrow";
    r.innerHTML = `<input class="an" maxlength="60" placeholder="Rule, e.g. Deep work"><input class="ao" maxlength="120" placeholder="Short explanation (optional)">
      <select><option value="check">Done / not</option><option value="count">Count</option><option value="time">Minutes</option></select>
      <input class="at" type="number" min="0" step="any" inputmode="decimal" placeholder="target"><input class="au" maxlength="10" placeholder="unit"><button class="x" aria-label="Remove">✕</button>
      ${g.block ? `<span class="lk">Linked to the ${esc(shortOf(g.block))} block${g.workout ? " · opens the guided workout" : ""}</span>` : ""}`;
    const [an, ao, at, au] = ["an", "ao", "at", "au"].map(c => r.querySelector("." + c)), ty = r.querySelector("select");
    an.value = g.name || ""; ao.value = g.note || ""; ty.value = g.type || "check"; at.value = g.type === "check" ? "" : (g.target ?? ""); au.value = g.unit || "";
    at.disabled = au.disabled = ty.value === "check";
    an.oninput = () => { g.name = an.value; }; ao.oninput = () => { g.note = ao.value; };
    ty.onchange = () => { g.type = ty.value; if (g.type === "time") { g.unit = "min"; g.step = 5; } if (g.type !== "check" && !(g.target > 0)) g.target = g.type === "time" ? 30 : 1; drawProgramEditor(key); };
    at.oninput = () => { g.target = Number(at.value) || 0; }; au.oninput = () => { g.unit = au.value; };
    r.querySelector(".x").onclick = () => { D.goals.splice(i, 1); drawProgramEditor(key); };
    rules.appendChild(r);
  });
  o.querySelector("#apAdd").onclick = () => { D.goals.push(newGoal()); drawProgramEditor(key); };
  const lib = o.querySelector("#apLib");
  GOAL_LIB.forEach(t => {
    const have = D.goals.some(g => g.id === t.id), c = document.createElement("button");
    c.className = "chipbtn"; c.disabled = have; c.textContent = (have ? "✓ " : "+ ") + t.name;
    c.onclick = () => { D.goals.push({...t}); drawProgramEditor(key); };
    lib.appendChild(c);
  });
  o.querySelector("#apSave").onclick = () => {
    const goals = D.goals.filter(g => (g.name || "").trim()).map(g => ({...g, name: g.name.trim(), note: (g.note || "").trim()}));
    if (!D.name.trim()) return toast("Give the program a name.");
    if (!goals.length) return toast("Add at least one rule.");
    const k = key || slug(D.name), fs = crewFS();
    const doc = {name: D.name.trim(), sub: D.sub.trim(), tag: D.strict ? "Strict · hosted" : "Hosted", length: Math.max(1, Math.min(365, Math.round(D.length) || 75)),
      strict: D.strict, hidden: D.hidden, goals, by: myEmail(), updated: firebase.firestore.FieldValue.serverTimestamp()};
    fs.db.collection("programs").doc(k).set(doc)
      .then(() => { admDraft = null; drawAdmin(); toast(`${doc.name} published. Members on it update now.`); })
      .catch(e => toast("Couldn't publish: " + e.message));
  };
}

/* ---------- boot ---------- */
$("brandMark").innerHTML = BRAND_SVG;''')

open(P, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
