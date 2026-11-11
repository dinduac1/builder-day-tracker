"""One-off: plan the week by body areas (one or more per day), e.g. Mon Upper body + Back, Sun Pelvic floor.
A day's plan is a saved set key, "rest", or "areas:A|B" drawn from your Full body set (or the library for areas it lacks)."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rep('''const workoutKeyFor = k => { const w = (days[k] && days[k].workout) || defaultWorkoutFor(k); return workouts()[w] ? w : "full"; };''',
'''const PLAN_AREAS = ["Upper body", "Back", "Core", "Legs & glutes", "Pelvic floor"];
const isAreaPlan = w => typeof w === "string" && w.startsWith("areas:");
const planAreas = w => isAreaPlan(w) ? w.slice(6).split("|").filter(a => PLAN_AREAS.includes(a)) : [];
const areaPlanKey = areas => areas.length ? "areas:" + PLAN_AREAS.filter(a => areas.includes(a)).join("|") : "rest";
const workoutKeyFor = k => { const w = (days[k] && days[k].workout) || defaultWorkoutFor(k); return workouts()[w] || (isAreaPlan(w) && planAreas(w).length) ? w : "full"; };
/** What a plan entry means: a saved set, or chosen areas taken from your Full body set (library for areas it doesn't have). */
function resolveWorkout(key){
  const W = workouts();
  if (isAreaPlan(key)) {
    const areas = planAreas(key), base = (W.full && W.full.items) || [], lib = exLibrary();
    const items = areas.flatMap(a => { const mine = base.filter(r => r.sec === a); return (mine.length ? mine : lib.filter(r => r.sec === a)).map(r => ({...r})); });
    return {key, name: areas.join(" + "), focus: `${areas.length} area${areas.length > 1 ? "s" : ""} · ${items.length} exercises`, items, areas: true};
  }
  const w = W[key] || W.full;
  return {key: W[key] ? key : "full", ...w};
}
const WEEK_TEMPLATES = [
  {name: "2 areas a day", sub: "Upper + Back · Core + Legs · Sun pelvic floor", plan: ["areas:Upper body|Back", "areas:Core|Legs & glutes", "areas:Upper body|Back", "areas:Core|Legs & glutes", "areas:Upper body|Back", "areas:Core|Legs & glutes", "areas:Pelvic floor"]},
  {name: "Full body", sub: "Everything Mon–Sat · Sun rest", plan: ["full", "full", "full", "full", "full", "full", "rest"]},
  {name: "Upper / Lower", sub: "Upper + Back · Legs + Core, 2 rest days", plan: ["areas:Upper body|Back", "areas:Core|Legs & glutes", "rest", "areas:Upper body|Back", "areas:Core|Legs & glutes", "areas:Upper body|Back|Core|Legs & glutes", "rest"]},
];''')
rep('''    const wk = workoutKeyFor(k), W = workouts();
    const gs = [{key:"w:" + wk, label:W[wk].name, title:`${W[wk].name} · ${W[wk].focus}`, items:W[wk].items}];
    if (wk !== "rest" && W.core.items.length) gs.push''', '''    const wk = workoutKeyFor(k), W = workouts(), R = resolveWorkout(wk);
    const gs = [{key:(R.areas ? "a:" : "w:") + wk, label:R.name, title:`${R.name} · ${R.focus}`, items:R.items}];
    if (wk !== "rest" && W.core.items.length) gs.push''')
rep('''    const wk = workoutKeyFor(sel), W = workouts();
    const bar = document.createElement("div"); bar.className = "wsel";
    bar.innerHTML = `<label class="fl" for="wsel">Workout</label><select id="wsel" class="ed">${setKeys().map(k => `<option value="${k}">${esc(W[k].name)} · ${esc(W[k].focus || "")}</option>`).join("")}</select>`;''',
'''    const wk = workoutKeyFor(sel), W = workouts();
    const bar = document.createElement("div"); bar.className = "wsel";
    const opts = [...new Set([defaultWorkoutFor(sel), wk, ...split().filter(isAreaPlan), ...PLAN_AREAS.map(a => "areas:" + a), ...setKeys()])].filter(k => k === "rest" || W[k] || isAreaPlan(k));
    bar.innerHTML = `<label class="fl" for="wsel">Workout</label><select id="wsel" class="ed">${opts.map(k => { const R = resolveWorkout(k); return `<option value="${esc(k)}">${esc(k === "rest" ? "Rest" : R.name)}${k === defaultWorkoutFor(sel) ? " · today's plan" : ""}</option>`; }).join("")}</select>`;''')
rep('''    sp.textContent = "Week: " + DOW.map((n,i) => `${n} ${(W[split()[i]] || W.full).name}`).join(" · ");''',
    '''    sp.textContent = "Week: " + DOW.map((n,i) => `${n} ${split()[i] === "rest" ? "Rest" : resolveWorkout(split()[i]).name}`).join(" · ");''')
rep('''    link.textContent = g.items.length ? `Edit ${g.label} counters` : "+ Track reps";
    link.onclick = () => { editingReps = g.key; repDraft = g.items.map(r => ({...r})); if (!repDraft.length) repDraft.push(newRep()); render(); };''',
'''    link.textContent = g.key.startsWith("a:") ? "Change exercises or targets in Workout sets" : g.items.length ? `Edit ${g.label} counters` : "+ Track reps";
    link.onclick = g.key.startsWith("a:") ? () => openWorkouts("full") : () => { editingReps = g.key; repDraft = g.items.map(r => ({...r})); if (!repDraft.length) repDraft.push(newRep()); render(); };''')
rep('''      const W = workouts()[workoutKeyFor(sel)], items = repDefs("train", sel);''', '''      const W = resolveWorkout(workoutKeyFor(sel)), items = repDefs("train", sel);''')

# week planner: areas per day (any number), or a saved set, or rest; plus templates
rep('''  const wk = o.querySelector(".wweek"), keys = setKeys();
  DOW.forEach((dn, i) => {
    const r = document.createElement("label"); r.className = "wday";
    r.innerHTML = `<span>${dn}</span><select>${keys.map(k => `<option value="${k}">${esc(W[k].name)}</option>`).join("")}</select>`;
    const se = r.querySelector("select"); se.value = W[split()[i]] ? split()[i] : "full";
    se.onchange = () => { const sp = [...split()]; sp[i] = se.value; settings.split = sp; saveSettings(); };
    wk.appendChild(r);
  });''', '''  const wk = o.querySelector(".wweek"), keys = setKeys().filter(k => k !== "rest");
  const tp = document.createElement("div"); tp.className = "tpls";
  WEEK_TEMPLATES.forEach(T => { const c = document.createElement("button"); c.className = "tpl"; c.innerHTML = `<b></b><span></span>`; c.querySelector("b").textContent = T.name; c.querySelector("span").textContent = T.sub;
    c.onclick = () => { settings.split = [...T.plan]; saveSettings(); drawWorkouts(); toast(`${T.name} plan set.`); }; tp.appendChild(c); });
  wk.appendChild(tp);
  const note = document.createElement("p"); note.className = "beat"; note.style.margin = "4px 0"; note.textContent = "Tap the areas you train each day (as many as you like). Exercises and targets come from your Full body set.";
  wk.appendChild(note);
  DOW.forEach((dn, i) => {
    const e = split()[i], areas = planAreas(e);
    const r = document.createElement("div"); r.className = "wday2";
    r.innerHTML = `<div class="wdh"><b>${dn}</b><span></span></div><div class="chips2"></div><select class="wset"><option value="">Or a saved set…</option>${keys.map(k => `<option value="${k}">${esc(W[k].name)}</option>`).join("")}</select>`;
    const cnt = isAreaPlan(e) ? resolveWorkout(e).items.length : e === "rest" ? 0 : (W[e] || W.full).items.length;
    r.querySelector(".wdh span").textContent = e === "rest" ? "Rest" : `${isAreaPlan(e) ? areas.join(" + ") : (W[e] || W.full).name} · ${cnt} exercises`;
    const ch = r.querySelector(".chips2");
    const setDay = v => { const sp = [...split()]; sp[i] = v; settings.split = sp; saveSettings(); drawWorkouts(); };
    PLAN_AREAS.forEach(a => { const b = document.createElement("button"); b.className = "chipbtn" + (areas.includes(a) ? " on" : ""); b.textContent = a;
      b.onclick = () => setDay(areaPlanKey(areas.includes(a) ? areas.filter(x => x !== a) : [...areas, a])); ch.appendChild(b); });
    const rb = document.createElement("button"); rb.className = "chipbtn" + (e === "rest" ? " on" : ""); rb.textContent = "Rest"; rb.onclick = () => setDay("rest"); ch.appendChild(rb);
    const se = r.querySelector("select"); se.value = W[e] && e !== "rest" ? e : "";
    se.onchange = () => { if (se.value) setDay(se.value); };
    wk.appendChild(r);
  });''')
rep("</style>\n</head>", """.wday2{display:grid;gap:8px;padding:12px 0;border-bottom:1px solid var(--line)}
.wday2 .wdh{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.wday2 .wdh b{font-family:var(--f-display);font-weight:800;letter-spacing:.08em;text-transform:uppercase;font-size:18px}
.wday2 .wdh span{font-size:12.5px;color:var(--muted);text-align:right}
.wday2 .chipbtn{padding:7px 11px;font-size:12.5px}
.wday2 .wset{font:inherit;font-size:13px;padding:7px 10px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--muted);justify-self:start}
</style>
</head>""")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
