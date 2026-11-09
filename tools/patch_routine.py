"""One-off: personal routines (routine builder + library), workout sets built from areas,
75 Hard redefined around the Five, goal library, 75 Soft removed, and two bug fixes
(goal editor crash; choosing 75 Hard switched the schedule off)."""
import os, re
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()

def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n >= 1, "not found: " + a[:90]
    if count == 1: assert n == 1, f"{n} matches: " + a[:90]
    s = s.replace(a, b) if count == 0 else s.replace(a, b, 1)

# ---------------------------------------------------------------- CSS
rep("</style>\n</head>", r""".goal .gname .gnote{display:block;font-weight:400;font-size:12.5px;color:var(--muted);margin-top:2px}
.goal .gacts{grid-column:2 / -1;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center}
.chips2{display:flex;flex-wrap:wrap;gap:8px}
.chipbtn{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:8px 13px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
.chipbtn:hover{border-color:var(--line-strong)}
.chipbtn.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.chipbtn.part{border-color:var(--accent);color:var(--accent)}
.chipbtn:disabled{opacity:.45;cursor:default}
.chipbtn small{font-family:var(--f-mono);font-weight:500;font-size:11px;opacity:.8;margin-left:4px}
.tpls{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.tpl{text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:14px;padding:12px 14px;cursor:pointer;color:var(--ink);display:grid;gap:2px;font-family:inherit}
.tpl b{font-size:14.5px}.tpl span{font-size:12px;color:var(--muted)}
.tpl:hover{border-color:var(--accent)}
.rlist{display:grid}
.rrow{display:grid;grid-template-columns:96px 96px minmax(0,1fr) 38px 38px;gap:6px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)}
.rrow .rn{grid-column:1 / 4;grid-row:1;font-weight:600}
.rrow .star{grid-column:4;grid-row:1}.rrow .x{grid-column:5;grid-row:1}
.rrow .rs{grid-column:1;grid-row:2}.rrow .re{grid-column:2;grid-row:2}.rrow .rd{grid-column:3 / 6;grid-row:2}
.rrow input{font:inherit;font-size:13.5px;padding:8px 9px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);min-width:0;width:100%}
.rrow .rn{font-size:15px}
.rrow button{height:36px;border-radius:9px;border:1px solid var(--line);background:var(--bg);cursor:pointer;font-size:15px;color:var(--muted)}
.rrow .star[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.rrow .x{color:var(--warn)}
.libcat{display:grid;gap:8px;margin-bottom:6px}
.libcat h4{margin:6px 0 0;font-family:var(--f-mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:500}
.savebar{position:sticky;bottom:0;display:flex;gap:10px;padding:14px 0 calc(env(safe-area-inset-bottom,0px) + 6px);background:var(--bg);border-top:1px solid var(--line);z-index:2}
.savebar .btn{flex:1}
.wcard{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px;align-items:center;padding:14px 16px;border:1px solid var(--line);border-radius:16px;background:var(--surface)}
.wcard b{font-size:16px}.wcard span{grid-column:1;font-size:12.5px;color:var(--muted)}
.wcard .acts{grid-row:1 / span 2;grid-column:2;display:flex;gap:12px}
.wweek{display:grid;gap:6px}
.wday{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;align-items:center;font-family:var(--f-mono);font-size:12px;color:var(--muted)}
.wday select,.wname{font:inherit;font-size:14px;padding:9px 10px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--ink);width:100%;min-width:0}
.wname{font-size:18px;font-weight:600;padding:12px 14px}
.wex{display:grid;grid-template-columns:28px minmax(0,1fr) 64px 18px;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid var(--line)}
.wex .rname{background:none;border:0;padding:0;text-align:left;color:var(--ink);font:inherit;font-size:14px;cursor:pointer}
.wex input[type=number]{font:inherit;font-size:13px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);width:100%;min-width:0;text-align:right}
.wex .u{font-family:var(--f-mono);font-size:11px;color:var(--muted)}
.wex.off .rname{color:var(--muted)}
@media (max-width:560px){
  .gedrow{grid-template-columns:minmax(0,1fr) 72px 64px 34px}
  .gedrow .gn{grid-column:1 / -1}
  .redhead[style*="108px"]{display:none!important}
}
</style>
</head>""")

# ---------------------------------------------------------------- HTML
rep('<div class="phead"><h2>The Five</h2>', '<div class="phead"><h2 id="fiveTitle">The Five</h2>')
rep('<ul class="tl" id="tl"></ul>', '<ul class="tl" id="tl"></ul>\n        <div class="redfoot" style="padding-top:14px"><button class="linkbtn" id="editRoutine">Edit your routine</button><button class="linkbtn" id="editWorkouts">Workout sets</button></div>')

# ---------------------------------------------------------------- routine model
rep("const BLOCKS = [\n", "const DEFAULT_BLOCKS = [\n")
rep('const FIVE = ["train","build","publish","connect","review"];\nconst SHORT = {train:"TRAIN",build:"BUILD",publish:"PUBLISH",connect:"CONNECT",review:"REVIEW"};',
'''const BLOCKS = DEFAULT_BLOCKS.map(b => ({...b}));   // the person's own routine (settings.blocks), kept in step by syncRoutine()
const FIVE = DEFAULT_BLOCKS.filter(b => b.five).map(b => b.id);   // their starred core blocks''')

rep("const CLOCK = new Set(BLOCKS.filter(b => b.clock).map(b => b.id));", r'''const CLOCK = new Set(BLOCKS.filter(b => b.clock).map(b => b.id));
function syncRoutine(){
  const src = Array.isArray(settings.blocks) && settings.blocks.length ? settings.blocks : DEFAULT_BLOCKS;
  BLOCKS.splice(0, BLOCKS.length, ...src.map(b => ({...b})));
  FIVE.splice(0, FIVE.length, ...BLOCKS.filter(b => b.five).map(b => b.id));
  CLOCK.clear(); BLOCKS.filter(b => b.clock).forEach(b => CLOCK.add(b.id));
}
const NUMW = ["None","The One","The Two","The Three","The Four","The Five","The Six","The Seven","The Eight","The Nine","The Ten"];
const fiveName = () => NUMW[FIVE.length] || "The Core";
const shortOf = id => ((BLOCKS.find(b => b.id === id) || DEFAULT_BLOCKS.find(b => b.id === id) || {name: id}).name.split(/ — | · | - /)[0].toUpperCase().slice(0, 16));
const fullFive = d => FIVE.length > 0 && fiveCount(d) === FIVE.length;''')

s = s.replace("SHORT[f]", "shortOf(f)")
rep("function streakEnding(k){ let n = 0; while (fiveCount(getDay(k)) === 5) {", "function streakEnding(k){ let n = 0; while (fullFive(getDay(k))) {")

# scoring
rep("  const five = fiveCount(d) / 5;\n", "  const five = FIVE.length ? fiveCount(d) / FIVE.length : null;\n")
rep("    {label:\"Daily Five done\", max:50, frac:five, note:`${fiveCount(d)}/5`},", "    {label:`${fiveName()} done`, max:50, frac:five, note:`${fiveCount(d)}/${FIVE.length}`},")
rep("    {label:\"Never missed twice\", max:10, frac:1 - doubles / 5,", "    {label:\"Never missed twice\", max:10, frac:FIVE.length ? 1 - doubles / FIVE.length : null,")
rep("  const five = scorable.reduce((s,k) => s + fiveCount(getDay(k)), 0) / (5*n);", "  const five = FIVE.length ? scorable.reduce((s,k) => s + fiveCount(getDay(k)), 0) / (FIVE.length*n) : null;")
rep("    {label:\"Daily Five done\", max:50, frac:five, note:`${Math.round(five*5*n)}/${5*n}`},", "    {label:`${fiveName()} done`, max:50, frac:five, note:`${Math.round((five || 0)*FIVE.length*n)}/${FIVE.length*n}`},")
rep("frac:Math.max(0, 1 - doubles/5),", "frac:FIVE.length ? Math.max(0, 1 - doubles/FIVE.length) : null,")

# render: sync + resilience
rep('''function render(){
  const today = keyOf(new Date());
  const day = getDay(sel);
  const d = fromKey(sel);
  applyLayout();
  renderHero(today);
  renderGoals(today);
  if (!useSchedule()) { const rv = $("review"); if (!editing() || !rv.contains(document.activeElement)) { rv.innerHTML = ""; rv.appendChild(reviewBlock(day)); } }
  pushCrew(); renderCrew();''', '''const safe = fn => { try { fn(); } catch(e) { console.error(e); } };   // one broken panel must never blank the rest
function render(){
  migrateProfile();
  syncRoutine();
  const today = keyOf(new Date());
  const day = getDay(sel);
  const d = fromKey(sel);
  applyLayout();
  safe(() => renderHero(today));
  safe(() => renderGoals(today));
  if (!useSchedule()) safe(() => { const rv = $("review"); if (!editing() || !rv.contains(document.activeElement)) { rv.innerHTML = ""; rv.appendChild(reviewBlock(day)); } });
  safe(() => { pushCrew(); renderCrew(); });
  $("fiveTitle").textContent = fiveName();''')
rep('''  $("fiveScore").innerHTML = `${fc}<small>/5</small>`;
  const sk = fc === 5 ? streakEnding(sel) : streakEnding(shift(sel,-1));''', '''  $("fiveScore").innerHTML = `${fc}<small>/${FIVE.length}</small>`;
  const sk = fullFive(day) ? streakEnding(sel) : streakEnding(shift(sel,-1));''')
rep('  if (fc === 5) add("All Five done. The day is won.", true);', '  if (fullFive(day)) add(`All of ${fiveName()} done. The day is won.`, true);')
rep('''  renderDayScore(today);
  renderAcct(today);
  renderWeek(today);
''', '''  safe(() => renderDayScore(today));
  safe(() => renderAcct(today));
  safe(() => renderWeek(today));
''')
rep("  renderHeat(today);\n}", "  safe(() => renderHeat(today));\n}")
# heat
rep("    b.style.background = `var(--heat${fc})`;\n    b.title = `${fromKey(k).toLocaleDateString(undefined,{weekday:\"short\",day:\"numeric\",month:\"short\"})}: ${fc}/5`;",
    "    b.style.background = `var(--heat${FIVE.length ? Math.round(fc / FIVE.length * 5) : 0})`;\n    b.title = `${fromKey(k).toLocaleDateString(undefined,{weekday:\"short\",day:\"numeric\",month:\"short\"})}: ${fc}/${FIVE.length}`;")
rep("  const keys = Object.keys(days).filter(k => fiveCount(days[k]) === 5).sort();", "  const keys = Object.keys(days).filter(k => fullFive(days[k])).sort();")
# report
rep("    out.push(`${B(\"THE FIVE\")}  ${fiveCount(d)}/5\\n`", "    if (FIVE.length) out.push(`${B(fiveName().toUpperCase())}  ${fiveCount(d)}/${FIVE.length}\\n`")
rep("      const v = (d.goals || {})[goal.id];\n      const ok = goalDone(goal, v);", "      const v = goalVal(k, goal);\n      const ok = goalDone(goal, v);")
rep("  if (useSchedule()) chip(`The Five <b>${fiveCount(getDay(sel))}/5</b>`);", "  if (useSchedule() && FIVE.length) chip(`${fiveName()} <b>${fiveCount(getDay(sel))}/${FIVE.length}</b>`);")

# toggle: a ticked Five block also completes the 75 Hard rule linked to it
rep("function toggle(id, on){ if (on) blockStarted(id); const d = ensure(sel); d.done = {...d.done, [id]: on}; saveDay(d,false); render(); }",
'''function toggle(id, on){
  if (on) blockStarted(id);
  const before = goalsDoneSet(sel), wasAll = goalProgress(sel).frac >= 1;
  const d = ensure(sel); d.done = {...d.done, [id]: on}; saveDay(d,false);
  announceGoals(before, wasAll);
  render();
}''')

# ---------------------------------------------------------------- workouts
rep('''  rest: {name:"Rest", focus:"Walk · mobility · recover", items:[
    {id:"mobility", name:"Mobility / stretching (minutes)", target:20},
    {id:"steps",    name:"Walk (thousand steps)",   target:8}]},
  push:''', '''  rest: {name:"Rest", focus:"Walk · mobility · recover", items:[
    {id:"mobility", name:"Mobility / stretching (minutes)", target:20},
    {id:"steps",    name:"Walk (thousand steps)",   target:8}]},
};
const OLD_GYM_WORKOUTS = {   // the old gym split; only shown to people who still have it saved
  push:''')
rep("const SPLIT_KEYS = [\"full\",\"rest\",\"push\",\"pull\",\"legs\"];\n", "")
rep("const workouts = () => Object.assign({}, DEFAULT_WORKOUTS, settings.workouts || {});",
'''const workouts = () => Object.assign({}, DEFAULT_WORKOUTS, settings.workouts || {});
const setKeys = () => { const W = workouts(); return Object.keys(W).filter(k => k !== "core" && k !== "rest" && W[k] && W[k].items).concat("rest"); };
const estMin = items => Math.round(items.reduce((t, r) => t + (r.unit === "sec" ? r.target : r.target * 3) + restSecs(), 0) / 60);''')
rep("const workoutKeyFor = k => (days[k] && days[k].workout) || defaultWorkoutFor(k);",
    "const workoutKeyFor = k => { const w = (days[k] && days[k].workout) || defaultWorkoutFor(k); return workouts()[w] ? w : \"full\"; };")
rep("    bar.innerHTML = `<label class=\"fl\" for=\"wsel\">Workout</label><select id=\"wsel\" class=\"ed\">${SPLIT_KEYS.map(k => `<option value=\"${k}\">${W[k].name} · ${W[k].focus}</option>`).join(\"\")}</select>`;",
    "    bar.innerHTML = `<label class=\"fl\" for=\"wsel\">Workout</label><select id=\"wsel\" class=\"ed\">${setKeys().map(k => `<option value=\"${k}\">${esc(W[k].name)} · ${esc(W[k].focus || \"\")}</option>`).join(\"\")}</select>`;")
rep('''    sp.textContent = "Week: " + DOW.map((n,i) => `${n} ${W[split()[i]].name}`).join(" · ");
    ex.append(bar, sp);''', '''    sp.textContent = "Week: " + DOW.map((n,i) => `${n} ${(W[split()[i]] || W.full).name}`).join(" · ");
    const wl = document.createElement("button"); wl.className = "linkbtn"; wl.textContent = "Build workout sets · plan your week";
    wl.onclick = () => openWorkouts();
    ex.append(bar, sp, wl);''')
rep("      const mins = Math.round(items.reduce((t, r) => t + (r.unit === \"sec\" ? r.target : r.target * 3) + restSecs(), 0) / 60);",
    "      const mins = estMin(items);")
rep('''  if (player.goalId && mins > 0) {''', '''  const pg = player.goalId && goalsList().find(g => g.id === player.goalId);
  if (pg && pg.type === "time" && mins > 0) {''')

# ---------------------------------------------------------------- reminders carry the routine
rep("body: JSON.stringify({subscription: sub.toJSON(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, blocks: remindBlocks()})});",
    "body: JSON.stringify({subscription: sub.toJSON(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone, blocks: remindBlocks(),\n      routine: BLOCKS.map(b => ({id: b.id, s: b.s, name: b.name, desc: b.desc || \"\"}))})});")

# ---------------------------------------------------------------- programs, goal library, linked goals
i = s.index("const PROGRAMS = {"); j = s.index("const goalDone =", i)
s = s[:i] + r'''// Goals people can add. The five "h_" goals are linked to the matching routine block: ticking either ticks both.
const GOAL_LIB = [
  {id:"h_train", block:"train", icon:"dumbbell", short:"Workout", name:"Complete your workout", note:"Your guided workout set for today.", type:"check", workout:true},
  {id:"h_build", block:"build", icon:"focus", short:"Deep work", name:"Deep work", note:"Your most valuable work, phone in another room.", type:"check"},
  {id:"h_publish", block:"publish", icon:"publish", short:"Publish", name:"Create & publish content", note:"Make it and ship it today.", type:"check"},
  {id:"h_connect", block:"connect", icon:"outreach", short:"Outreach", name:"Outreach", note:"Chase (cold DMs, emails, calls) or attract (ads, offers).", type:"check"},
  {id:"h_review", block:"review", icon:"review", short:"Review", name:"Evening review", note:"Score the day. Set tomorrow's top 3.", type:"check"},
  {id:"water", icon:"glass", short:"Water", name:"Drink your water minimum", type:"count", target:3, unit:"L", step:0.25},
  {id:"photo", icon:"camera", short:"Photo", name:"Take a progress photo", type:"check"},
  {id:"read", icon:"book", short:"Read", name:"Read 10 pages", type:"count", target:10, unit:"pages", step:1},
  {id:"study", icon:"book", short:"Study", name:"Study your craft", type:"time", target:30, unit:"min", step:5},
  {id:"steps", icon:"count", short:"Steps", name:"Walk 10,000 steps", type:"count", target:10, unit:"k steps", step:1},
  {id:"diet", icon:"plate", short:"Diet", name:"Follow your diet. No cheat meals", type:"check"},
  {id:"alcohol", icon:"nobottle", short:"No alcohol", name:"No alcohol", type:"check"},
  {id:"sleep7", icon:"clock", short:"Sleep", name:"Sleep 7+ hours", type:"check"},
  {id:"meditate", icon:"clock", short:"Pray", name:"Pray or meditate", type:"time", target:10, unit:"min", step:5},
  {id:"journal", icon:"book", short:"Journal", name:"Journal", type:"check"},
  {id:"nofeeds", icon:"check", short:"No feeds", name:"No social feeds before noon", type:"check"},
];
const libGoal = id => ({...GOAL_LIB.find(g => g.id === id)});
const PROGRAMS = {
  "75hard": {name:"75 Hard", tag:"Strict · with your crew", sub:"The Five every day (workout, deep work, create & publish, outreach, review), your water minimum and a progress photo. 75 days. Miss one and you're back to Day 1.",
    challenge:{name:"75 Hard", length:75, strict:true},
    goals:["h_train","h_build","h_publish","h_connect","h_review","water","photo"].map(libGoal)},
  "builder": {name:"Build your day", tag:"Timed routine", sub:"Your own timed routine: start from the Builder Day or another template, add blocks from the library, star your core. Times, reps, records and alarms.", schedule:true, goals:[]},
  "custom": {name:"Your own goals", tag:"Blank", sub:"Pick daily goals from the library or write your own.", goals:[]},
};
/** A goal's value for a day. Linked goals read their routine block's tick. */
function goalVal(k, g){
  const d = getDay(k);
  if (g.block && d.done && d.done[g.block]) return g.type === "check" ? true : Math.max(Number((d.goals || {})[g.id]) || 0, Number(g.target) || 0);
  return (d.goals || {})[g.id];
}
const goalsDoneSet = k => new Set(goalsList().filter(g => goalDone(g, goalVal(k, g))).map(g => g.id));
/** After a change on the selected day: tell the crew about goals that just got done. */
function announceGoals(before, wasAll){
  if (sel !== keyOf(new Date())) return;
  const newly = goalsList().filter(g => !before.has(g.id) && goalDone(g, goalVal(sel, g)));
  if (!newly.length) return;
  const cs = challengeState(sel);
  if (!wasAll && goalProgress(sel).frac >= 1) crewEvent(cs ? `completed Day ${cs.dayN} of ${cs.name}. Every rule done.` : "finished every goal today.");
  else newly.forEach(g => crewEvent(`finished “${g.name}”${cs ? ` · Day ${cs.dayN}` : ""}.`));
}
/** Older saved setups: the first 75 Hard rules and 75 Soft. */
function migrateProfile(){
  const p = settings.profile; if (!p) return;
  let ch = false;
  if (p.program === "75hard" && goalsList().some(g => g.id === "w_out")) {
    settings.goals = PROGRAMS["75hard"].goals.map(g => ({...g}));
    // picking 75 Hard used to switch the timed schedule off; give it back to anyone who was using it
    if (p.schedule === false && Object.values(days).some(d => doneCount(d) > 0)) settings.profile = {...p, schedule: true};
    ch = true;
  }
  if (p.program === "75soft") { settings.profile = {...settings.profile, program: "custom"}; ch = true; }
  if (ch) saveSettings();
}
''' + s[j:]
rep('''  const done = G.filter(g => goalDone(g, gv[g.id])).length;''', '''  const done = G.filter(g => goalDone(g, goalVal(k, g))).length;''')
rep('''function setGoal(id, v){
  const d = ensure(sel), g = goalsList().find(x => x.id === id), wasDone = g && goalDone(g, (d.goals || {})[id]), wasAll = goalProgress(sel).frac >= 1;
  d.goals = {...(d.goals || {})};
  if (v === null || v === false || v === 0) delete d.goals[id]; else d.goals[id] = v;
  saveDay(d, false);
  if (sel === keyOf(new Date()) && g && !wasDone && goalDone(g, d.goals[id])) {
    const cs = challengeState(sel);
    if (!wasAll && goalProgress(sel).frac >= 1) crewEvent(cs ? `completed Day ${cs.dayN} of ${cs.name}. Every rule done.` : "finished every goal today.");
    else crewEvent(`finished “${g.name}”${cs ? ` · Day ${cs.dayN}` : ""}.`);
  }
  render();
}''', '''function setGoal(id, v){
  const g = goalsList().find(x => x.id === id), before = goalsDoneSet(sel), wasAll = goalProgress(sel).frac >= 1;
  const d = ensure(sel);
  d.goals = {...(d.goals || {})};
  if (v === null || v === false || v === 0) delete d.goals[id]; else d.goals[id] = v;
  if (g && g.block && g.type === "check") { d.done = {...d.done, [g.block]: !!v}; delete d.goals[id]; if (v) blockStarted(g.block); }
  saveDay(d, false);
  announceGoals(before, wasAll);
  render();
}''')
rep('''function applyProgram(key, startToday){
  const P = PROGRAMS[key];
  settings.profile = {...profile(), program: key, schedule: !!P.schedule || (key === "builder")};
  if (key === "builder") settings.profile.schedule = true;''', '''function applyProgram(key, startToday){
  const P = PROGRAMS[key];
  editingGoals = false;
  settings.profile = {...profile(), program: key};   // a challenge never switches your timed routine off
  if (P.schedule) settings.profile.schedule = true;''')

# goals panel
rep('''    ["75hard", "75soft", "custom"].forEach(k => {
      const P = PROGRAMS[k], c = document.createElement("button"); c.className = "prog-card";''', '''    ["75hard", "custom"].forEach(k => {
      const P = PROGRAMS[k], c = document.createElement("button"); c.className = "prog-card";''')
rep('''  G.forEach((g, i) => {
    const v = gv[g.id], done = goalDone(g, v);''', '''  G.forEach((g, i) => {
    const v = goalVal(sel, g), done = goalDone(g, v);''')
rep('''      plus.onclick = () => setGoal(g.id, Math.round((n + step) * 100) / 100);
      if (g.workout && sel === today) {
        const w = document.createElement("button"); w.className = "linkbtn gwork"; w.textContent = "▶ Guided workout · logs the minutes here";
        w.onclick = () => { pendingGoalId = g.id; startWorkout(repDefs("train", today)); };
        row.appendChild(w);
      }
    }
    row.querySelector(".gname").textContent = g.name;''', '''      plus.onclick = () => setGoal(g.id, Math.round((n + step) * 100) / 100);
    }
    const gn = row.querySelector(".gname"); gn.textContent = g.name;
    if (g.note) { const nt = document.createElement("small"); nt.className = "gnote"; nt.textContent = g.note; gn.appendChild(nt); }
    if (g.workout) {
      const acts = document.createElement("div"); acts.className = "gacts";
      const W = workouts()[workoutKeyFor(sel)], items = repDefs("train", sel);
      if (sel === today && items.length && workoutKeyFor(sel) !== "rest") {
        const w = document.createElement("button"); w.className = "linkbtn gwork";
        w.textContent = `▶ ${W.name} · ${items.length} exercises · ~${estMin(items)} min`;
        w.onclick = () => { pendingGoalId = g.id; startWorkout(items); };
        acts.appendChild(w);
      }
      const cw = document.createElement("button"); cw.className = "linkbtn"; cw.textContent = "Workout sets";
      cw.onclick = () => openWorkouts();
      acts.appendChild(cw);
      row.appendChild(acts);
    }''')
rep('''    const [nm, , tg, un] = r.querySelectorAll("input"), ty = r.querySelector("select");''', '''    const [nm, tg, un] = r.querySelectorAll("input"), ty = r.querySelector("select");''')
rep('''  const hint = document.createElement("p"); hint.className = "beat";
  hint.textContent = "Change your challenge, or start one, in Settings (the sliders at the top).";
  w.appendChild(hint);''', '''  const lib = document.createElement("div"); lib.className = "libcat";
  lib.innerHTML = `<h4>Quick add</h4><div class="chips2"></div>`;
  GOAL_LIB.forEach(t => {
    const c = document.createElement("button"), have = goalDraft.some(g => g.id === t.id);
    c.className = "chipbtn"; c.textContent = (have ? "✓ " : "+ ") + t.name; c.disabled = have;
    c.onclick = () => { goalDraft = goalDraft.filter(g => g.name.trim()); goalDraft.push({...t}); render(); };
    lib.querySelector(".chips2").appendChild(c);
  });
  w.appendChild(lib);
  const hint = document.createElement("p"); hint.className = "beat";
  hint.textContent = "Workout, deep work, publish, outreach and review are linked to the same blocks in your routine: tick either one. Start or change a challenge in Settings.";
  w.appendChild(hint);''')

# layout: send the routine to the phone app / reminder server when it changes
rep('''  if (NATIVE && NATIVE.setScheduleEnabled && lastNativeSchedule !== sch) { try { NATIVE.setScheduleEnabled(sch); lastNativeSchedule = sch; } catch(e){} }''',
'''  if (NATIVE && NATIVE.setScheduleEnabled && lastNativeSchedule !== sch) { try { NATIVE.setScheduleEnabled(sch); lastNativeSchedule = sch; } catch(e){} }
  const sig = JSON.stringify(BLOCKS.map(b => [b.id, b.s, b.e, b.name, b.desc, !!b.five]));
  if (sig !== lastRoutineSig) {
    lastRoutineSig = sig;
    if (NATIVE && NATIVE.setRoutine) { try { NATIVE.setRoutine(JSON.stringify(BLOCKS.map(b => ({id: b.id, s: b.s, e: b.e, name: b.name, desc: b.desc || "", five: !!b.five})))); } catch(e){} }
    else if (typeof swReg !== "undefined" && swReg) currentSub().then(sub => sub && postSub(sub)).catch(() => {});
  }''')
rep("let lastNativeSchedule = null;", "let lastNativeSchedule = null, lastRoutineSig = null;")

# icons
rep("  check: '<svg viewBox=\"0 0 24 24\"", '''  focus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/></svg>',
  publish: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M7 8l5-5 5 5"/><path d="M4 14v5a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/></svg>',
  outreach: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 3 10 14"/><path d="M21 3l-7 18-4-7-7-4z"/></svg>',
  review: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2.5h6V4"/><path d="M9 12.5l2 2 4-4"/></svg>',
  check: '<svg viewBox="0 0 24 24"''')
rep('''        const ok = goalDone(g, gv[g.id]);''', '''        const ok = goalDone(g, goalVal(k, g));''')

# onboarding + settings
rep('''    ["75hard", "75soft", "builder", "custom"].forEach(k => {''', '''    ["75hard", "builder", "custom"].forEach(k => {''')
rep('''        if (k === "builder") { settings.profile = {...profile(), program: "builder", schedule: true}; settings.goals = []; settings.challenge = null; saveSettings(); onboarding("crew"); }''',
    '''        if (k === "builder") { settings.profile = {...profile(), program: "builder", schedule: true}; settings.goals = []; settings.challenge = null; saveSettings(); openRoutine(() => onboarding("crew")); }''')
rep('''        else { settings.profile = {...profile(), schedule: false}; applyProgram(k, true); onboarding("crew"); }''',
    '''        else { settings.profile = {...profile(), schedule: false}; applyProgram(k, true); onboarding("workout"); }''')
rep('''  } else if (step === "crew") {''', '''  } else if (step === "workout") {
    b.innerHTML = `<h2>Your workout.</h2><p class="lead">The ORDO workout trains every area: upper body, legs and glutes, core, back, then a stretch. Use all of it, or build your own sets from the areas you want.</p>
      <div style="display:grid;gap:10px"><button class="btn primary block" id="obAll">Use the full ORDO workout</button><button class="btn block" id="obBuild">Build my own sets</button></div>`;
    b.querySelector("#obAll").onclick = () => onboarding("crew");
    b.querySelector("#obBuild").onclick = () => openWorkouts(null, () => onboarding("crew"));
  } else if (step === "crew") {''')
rep('''    <div class="setgrp"><h3>Program</h3><div class="progs" id="stProgs"></div>
      <label class="toggle"><span>Timed daily schedule (Builder Day blocks, the Five, alarms)</span><input type="checkbox" id="stSched"></label></div>''',
'''    <div class="setgrp"><h3>Goals</h3><div class="progs" id="stProgs"></div></div>
    <div class="setgrp"><h3>Routine</h3>
      <label class="toggle"><span>Timed daily routine (your blocks, starred core, alarms)</span><input type="checkbox" id="stSched"></label>
      <div class="redfoot"><button class="btn-sm" id="stRoutine">Build / edit your routine</button><button class="linkbtn" id="stWorkouts">Workout sets</button></div></div>''')
rep('''  ["75hard", "75soft", "custom"].forEach(k => {
    const P = PROGRAMS[k], card = document.createElement("button"); card.className = "prog-card" + (p.program === k ? " on" : "");''',
'''  ["75hard", "custom"].forEach(k => {
    const P = PROGRAMS[k], card = document.createElement("button"); card.className = "prog-card" + (p.program === k ? " on" : "");''')
rep('''      card.onclick = () => { if (k === "custom") { settings.profile = {...profile(), program: "custom"}; settings.goals = []; settings.challenge = null; saveSettings(); } else applyProgram(k, true); openSettings(); };''',
    '''      card.onclick = () => { if (k === "custom") { settings.profile = {...profile(), program: "custom"}; settings.challenge = null; editingGoals = true; goalDraft = goalsList().map(g => ({...g})); if (!goalDraft.length) goalDraft.push(newGoal()); saveSettings(); closeOverlay(); render(); $("goalsPanel").scrollIntoView({behavior: "smooth"}); } else { applyProgram(k, true); openSettings(); } };''')
rep('''  sch.onchange = () => { settings.profile = {...profile(), schedule: sch.checked}; saveSettings(); };''',
'''  sch.onchange = () => { settings.profile = {...profile(), schedule: sch.checked}; saveSettings(); if (sch.checked && !settings.blocks && profile().program !== "builder" && !Object.values(days).some(d => doneCount(d) > 0)) openRoutine(); };
  o.querySelector("#stRoutine").onclick = () => openRoutine();
  o.querySelector("#stWorkouts").onclick = () => openWorkouts();''')

# ---------------------------------------------------------------- builders
rep("/* ---------- boot ---------- */\n$(\"brandMark\").innerHTML = BRAND_SVG;", r'''/* =========================================================== routine builder */
const esc = t => String(t == null ? "" : t).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
// Blocks people can add. Taken from the Builder Day, plus more. Ids that match the Builder Day keep its sounds and links.
const ROUTINE_LIB = [
  {cat:"Morning", items:[
    {id:"wake", name:"Wake", min:30, clock:true, desc:"Water, light, no phone. Read tonight's plan from last night."},
    {id:"pray", name:"Prayer / meditation", min:15, desc:"Quiet first. Gratitude, scripture or breath work."},
    {id:"journal", name:"Journal", min:10, desc:"Three lines: how I feel, what matters today, the win I'm chasing."},
    {id:"plan", name:"Plan the day", min:10, desc:"Check today's top 3. Give each one a time."},
    {id:"coldshower", name:"Cold shower", min:10, desc:"Two minutes cold at the end. Done before the excuses start."}]},
  {cat:"Body", items:[
    {id:"train", name:"TRAIN", min:75, five:true, desc:"Your guided workout. Log the session."},
    {id:"walk", name:"Walk", min:30, desc:"Outside, no calls. 3–4k steps."},
    {id:"run", name:"Run", min:40, desc:"An easy pace you could talk at. Build the base."},
    {id:"mobility", name:"Stretch & mobility", min:15, desc:"Hips, hamstrings, shoulders. Slow breathing."},
    {id:"mealprep", name:"Meal prep", min:45, desc:"Cook for the next two days. Protein first."}]},
  {cat:"Work", items:[
    {id:"build", name:"BUILD — Deep Work", min:120, five:true, desc:"Client delivery / product building / the money-making work. Phone in another room."},
    {id:"publish", name:"PUBLISH — Create & ship", min:90, five:true, desc:"Create + ship today's content. One long-form or one video, repurposed into 2–3 short pieces."},
    {id:"connect", name:"CONNECT — Outreach", min:45, five:true, desc:"Chase: cold DMs, emails, calls. Attract: ads and offers that pull leads in. Follow-ups first."},
    {id:"ads", name:"Ads & attraction", min:45, desc:"Launch, check or improve one ad or offer. Read the numbers."},
    {id:"sales", name:"Sales calls", min:60, desc:"Booked calls and follow-ups. Ask for the decision."},
    {id:"exec", name:"Execution block", min:180, desc:"More client work, sales calls, building systems, editing."},
    {id:"lunch", name:"Lunch + admin", min:60, desc:"Emails, invoices, small tasks batched here — never in deep work."},
    {id:"job", name:"Day job", min:480, desc:"Do it well. Use the lunch break for one core task."}]},
  {cat:"Mind", items:[
    {id:"study", name:"Study", min:30, desc:"30 min reading in the craft (sales, marketing, AI, psychology of teaching)."},
    {id:"drills", name:"Learning/skill drills", min:60, desc:"Deliberate practice on the weakest part of your craft."},
    {id:"read", name:"Read", min:20, desc:"10+ pages of a book that makes you better."},
    {id:"classes", name:"Classes / course", min:240, desc:"Be present. Take notes you'll actually use."},
    {id:"language", name:"Language practice", min:20, desc:"Speak it out loud. Small daily reps."}]},
  {cat:"Life", items:[
    {id:"break", name:"Break", min:30, desc:"Food. Walk. No feeds."},
    {id:"life", name:"Life", min:180, desc:"People, food, family, faith, community. You are building loyalty here too."},
    {id:"family", name:"Call family / a friend", min:20, desc:"One real conversation. Ask, then listen."},
    {id:"chores", name:"Chores & errands", min:45, desc:"Clean space, clear head. Batch them."},
    {id:"church", name:"Faith / church", min:90, desc:"Show up and serve."}]},
  {cat:"Evening", items:[
    {id:"review", name:"REVIEW", min:15, five:true, desc:"Scorecard (did I do the core?), write tomorrow's top 3, one line of gratitude."},
    {id:"wind", name:"Wind down", min:60, desc:"No screens after 21:30."},
    {id:"sleep", name:"Sleep", min:420, desc:"Excellence is a sleep-powered game. 7+ hours, non-negotiable."}]},
];
const libItem = id => { for (const c of ROUTINE_LIB) { const x = c.items.find(i => i.id === id); if (x) return x; } return null; };
const tb = (id, s, e, extra) => { const L = libItem(id); return {id, s, e, name: L.name, desc: L.desc, ...(L.five ? {five: true} : {}), ...(L.clock ? {clock: true} : {}), ...(extra || {})}; };
const DAY_TEMPLATES = {
  builder: {name: "Builder Day", sub: "14 blocks · the Five", blocks: () => DEFAULT_BLOCKS.map(b => ({...b}))},
  ninefive: {name: "9-to-5 builder", sub: "Job by day, build at night", blocks: () => [
    tb("wake", "05:30", "06:00"), tb("train", "06:00", "07:00"), tb("job", "08:00", "17:00"), tb("connect", "12:30", "13:00"),
    tb("life", "17:30", "18:30"), tb("build", "18:30", "20:00"), tb("publish", "20:00", "21:00"), tb("review", "21:15", "21:30"),
    tb("wind", "21:30", "22:30"), tb("sleep", "22:30", "05:30")]},
  student: {name: "Student", sub: "Classes, study, a side build", blocks: () => [
    tb("wake", "06:00", "06:30"), tb("train", "06:30", "07:30"), tb("classes", "08:00", "14:00"), tb("break", "14:00", "15:00"),
    tb("study", "15:00", "17:00", {five: true, desc: "Two focused hours on today's classes. Phone away."}), tb("build", "17:30", "19:00"),
    tb("life", "19:00", "21:00"), tb("review", "21:00", "21:15"), tb("wind", "21:30", "22:30"), tb("sleep", "22:30", "06:00")]},
  blank: {name: "Blank", sub: "Just wake and sleep", blocks: () => [tb("wake", "06:00", "06:30"), tb("sleep", "22:30", "06:00")]},
};
const addMins = (t, m) => clockFmt(mins(t) + m);
function sortRoutine(list){
  const w = list.find(b => b.id === "wake"), base = w ? mins(w.s) : 240;
  return list.slice().sort((a, b) => ((mins(a.s) - base + 1440) % 1440) - ((mins(b.s) - base + 1440) % 1440));
}
let rDraft = [], rAfter = null;
function openRoutine(after){
  rDraft = sortRoutine((Array.isArray(settings.blocks) && settings.blocks.length ? settings.blocks : DEFAULT_BLOCKS).map(b => ({...b})));
  rAfter = after || null;
  openOverlay(); drawRoutine();
}
function drawRoutine(){
  const o = ovl(), core = rDraft.filter(b => b.five).length;
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">Your routine</span><button class="close">✕ Close</button></div>
    <h2 class="exname">Build your day</h2>
    <p class="beat">Start from a template, then add blocks from the library or create your own. Star ★ the blocks that make your core: they're your daily non-negotiables, scored, streaked and nagged.</p>
    <div class="rgtitle">Start from</div><div class="tpls"></div>
    <div class="rgtitle">Your day · ${rDraft.length} blocks · ${core ? `${NUMW[core] || core + " core"} starred` : "none starred"}</div><div class="rlist"></div>
    <button class="btn block" id="rNew">+ Create your own block</button>
    <div class="rgtitle">Library · tap to add</div><div class="lib"></div>
    <div class="savebar"><button class="btn primary" id="rSave">Save routine</button><button class="btn" id="rCancel">Cancel</button></div></div>`;
  o.querySelector(".close").onclick = o.querySelector("#rCancel").onclick = () => { closeOverlay(); render(); };
  const tp = o.querySelector(".tpls");
  Object.entries(DAY_TEMPLATES).forEach(([k, T]) => {
    const c = document.createElement("button"); c.className = "tpl"; c.innerHTML = `<b>${esc(T.name)}</b><span>${esc(T.sub)}</span>`;
    c.onclick = () => { rDraft = sortRoutine(T.blocks()); drawRoutine(); toast(`${T.name} loaded. Change anything, then Save.`); };
    tp.appendChild(c);
  });
  const list = o.querySelector(".rlist");
  rDraft.forEach((b, i) => {
    const r = document.createElement("div"); r.className = "rrow";
    r.innerHTML = `<input class="rn" maxlength="40" placeholder="Block name" aria-label="Block name"><button class="star" aria-label="Core block">★</button><button class="x" aria-label="Remove">✕</button>
      <input class="rs" type="time" aria-label="Starts"><input class="re" type="time" aria-label="Ends"><input class="rd" maxlength="160" placeholder="What happens in this block" aria-label="Description">`;
    const [rn, rs, re, rd] = ["rn", "rs", "re", "rd"].map(c => r.querySelector("." + c));
    rn.value = b.name; rs.value = b.s; re.value = b.e; rd.value = b.desc || "";
    rn.oninput = () => { b.name = rn.value; }; rd.oninput = () => { b.desc = rd.value; };
    rs.onchange = () => { if (rs.value) { const len = slotLen(b); b.s = rs.value; b.e = addMins(rs.value, len); rDraft = sortRoutine(rDraft); drawRoutine(); } };
    re.onchange = () => { if (re.value) b.e = re.value; };
    const st = r.querySelector(".star"); st.setAttribute("aria-pressed", !!b.five); st.title = b.five ? "Core block (scored and nagged)" : "Make this a core block";
    st.onclick = () => { b.five = !b.five; if (!b.five) delete b.five; drawRoutine(); };
    r.querySelector(".x").onclick = () => { rDraft.splice(i, 1); drawRoutine(); };
    list.appendChild(r);
  });
  const nextStart = () => { const awake = rDraft.filter(b => b.id !== "sleep"); return awake.length ? awake[awake.length - 1].e : "07:00"; };
  o.querySelector("#rNew").onclick = () => {
    const s0 = nextStart(); rDraft.push({id: "b" + Date.now().toString(36), s: s0, e: addMins(s0, 60), name: "", desc: ""});
    rDraft = sortRoutine(rDraft); drawRoutine();
    const empty = [...ovl().querySelectorAll(".rn")].find(x => !x.value); if (empty) { empty.focus(); empty.scrollIntoView({block: "center"}); }
  };
  const lib = o.querySelector(".lib");
  ROUTINE_LIB.forEach(c => {
    const box = document.createElement("div"); box.className = "libcat"; box.innerHTML = `<h4>${c.cat}</h4><div class="chips2"></div>`;
    c.items.forEach(it => {
      const have = rDraft.some(b => b.id === it.id), btn = document.createElement("button");
      btn.className = "chipbtn"; btn.disabled = have;
      btn.innerHTML = `${have ? "✓" : "+"} ${esc(it.name)}${it.five ? " ★" : ""}<small>${fmt(it.min)}</small>`;
      btn.onclick = () => { const s0 = it.id === "wake" ? "05:00" : it.id === "sleep" ? "22:00" : nextStart(); rDraft.push(tb(it.id, s0, addMins(s0, it.min))); rDraft = sortRoutine(rDraft); drawRoutine(); toast(`Added ${it.name} at ${s0}. Adjust the time if you need to.`); };
      box.querySelector(".chips2").appendChild(btn);
    });
    lib.appendChild(box);
  });
  o.querySelector("#rSave").onclick = () => {
    const ok = rDraft.filter(b => (b.name || "").trim() && /^\d\d:\d\d$/.test(b.s) && /^\d\d:\d\d$/.test(b.e));
    if (!ok.length) return toast("Add at least one block with a name and times.");
    settings.blocks = sortRoutine(ok.map(b => ({...b, name: b.name.trim(), desc: (b.desc || "").trim()})));
    settings.profile = {...profile(), schedule: true};
    saveSettings(); closeOverlay(); render();
    toast("Routine saved."); if (rAfter) { const f = rAfter; rAfter = null; f(); }
  };
}

/* =========================================================== workout sets */
const AREAS = ["Upper body", "Legs & glutes", "Core", "Back", "Stretch", "Your own"];
function exLibrary(){
  const full = ((settings.workouts || {}).full || {}).items || [];
  const lib = ROUTINE.map(r => { const o = full.find(x => x.id === r.id); return {...r, target: o ? o.target : r.target}; });
  Object.values(settings.workouts || {}).forEach(w => (w.items || []).forEach(r => {
    if (!lib.some(x => x.id === r.id) && !["mobility", "steps"].includes(r.id)) lib.push({...r, sec: r.sec || (/stretch/i.test(r.name) ? "Stretch" : "Your own")});
  }));
  return lib.sort((a, b) => AREAS.indexOf(a.sec) - AREAS.indexOf(b.sec));
}
let wDraft = null, wAfter = null;
function openWorkouts(editKey, after){
  if (after) wAfter = after;
  openOverlay();
  if (editKey !== undefined && editKey !== null) return drawWorkoutEditor(editKey);
  drawWorkouts();
}
function finishWorkouts(){ closeOverlay(); render(); if (wAfter) { const f = wAfter; wAfter = null; f(); } }
function drawWorkouts(){
  const o = ovl(), W = workouts();
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">Workouts</span><button class="close">✕ Done</button></div>
    <h2 class="exname">Your workouts</h2>
    <p class="beat">The full ORDO workout trains every area. Build your own sets from the areas you want, then choose what you train each day.</p>
    <div class="progs" id="wsets"></div><button class="btn block" id="wNew">+ Build a new workout set</button>
    <div class="rgtitle">Your week</div><div class="wweek"></div></div>`;
  o.querySelector(".close").onclick = finishWorkouts;
  const box = o.querySelector("#wsets");
  setKeys().filter(k => k !== "rest").forEach(k => {
    const w = W[k], items = w.items || [], areas = AREAS.filter(a => items.some(r => r.sec === a));
    const c = document.createElement("div"); c.className = "wcard";
    c.innerHTML = `<b></b><span></span><div class="acts"><button class="linkbtn" data-a="edit">Edit</button>${k !== "full" ? '<button class="linkbtn" data-a="del" style="color:var(--warn)">Delete</button>' : ""}</div>`;
    c.querySelector("b").textContent = w.name;
    c.querySelector("span").textContent = `${items.length} exercises · ~${estMin(items)} min${areas.length ? " · " + areas.join(", ") : ""}`;
    c.querySelector("[data-a=edit]").onclick = () => drawWorkoutEditor(k);
    const del = c.querySelector("[data-a=del]");
    if (del) del.onclick = () => {
      if (del.dataset.sure) { const ws = {...settings.workouts}; delete ws[k]; settings.workouts = ws; settings.split = split().map(x => x === k ? "full" : x); saveSettings(); drawWorkouts(); }
      else { del.dataset.sure = "1"; del.textContent = "Tap to confirm"; }
    };
    box.appendChild(c);
  });
  o.querySelector("#wNew").onclick = () => drawWorkoutEditor(null);
  const wk = o.querySelector(".wweek"), keys = setKeys();
  DOW.forEach((dn, i) => {
    const r = document.createElement("label"); r.className = "wday";
    r.innerHTML = `<span>${dn}</span><select>${keys.map(k => `<option value="${k}">${esc(W[k].name)}</option>`).join("")}</select>`;
    const se = r.querySelector("select"); se.value = W[split()[i]] ? split()[i] : "full";
    se.onchange = () => { const sp = [...split()]; sp[i] = se.value; settings.split = sp; saveSettings(); };
    wk.appendChild(r);
  });
}
function drawWorkoutEditor(key){
  const lib = exLibrary(), W = workouts();
  if (!wDraft || wDraft.key !== key) {
    const cur = key && W[key] ? W[key].items : [];
    wDraft = {key, name: key && W[key] ? W[key].name : "", on: new Set(key ? cur.map(r => r.id) : []), target: Object.fromEntries(lib.map(r => [r.id, (cur.find(x => x.id === r.id) || r).target]))};
  }
  const o = ovl(), D = wDraft;
  const sel = lib.filter(r => D.on.has(r.id));
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">${key ? "Edit workout set" : "New workout set"}</span><button class="close">← Back</button></div>
    <input class="wname" maxlength="40" placeholder="Name it (e.g. Legs & core)">
    <div class="rgtitle">Areas · tap to add or remove a whole area</div><div class="chips2" id="wAreas"></div>
    <div class="chips2"><button class="chipbtn" id="wAll">Everything</button><button class="chipbtn" id="wNone">Clear</button></div>
    <div class="rgtitle">${sel.length} exercises · ~${estMin(sel.map(r => ({...r, target: D.target[r.id]})))} min</div><div id="wList"></div>
    <div class="savebar"><button class="btn primary" id="wSave">Save set</button><button class="btn" id="wCancel">Cancel</button></div></div>`;
  const back = () => { wDraft = null; drawWorkouts(); };
  o.querySelector(".close").onclick = o.querySelector("#wCancel").onclick = back;
  const nm = o.querySelector(".wname"); nm.value = D.name; nm.oninput = () => { D.name = nm.value; };
  const ar = o.querySelector("#wAreas");
  AREAS.forEach(a => {
    const inA = lib.filter(r => r.sec === a); if (!inA.length) return;
    const n = inA.filter(r => D.on.has(r.id)).length, b = document.createElement("button");
    b.className = "chipbtn" + (n === inA.length ? " on" : n ? " part" : "");
    b.innerHTML = `${esc(a)}<small>${n}/${inA.length}</small>`;
    b.onclick = () => { const all = n === inA.length; inA.forEach(r => all ? D.on.delete(r.id) : D.on.add(r.id)); drawWorkoutEditor(key); };
    ar.appendChild(b);
  });
  o.querySelector("#wAll").onclick = () => { lib.forEach(r => D.on.add(r.id)); drawWorkoutEditor(key); };
  o.querySelector("#wNone").onclick = () => { D.on.clear(); drawWorkoutEditor(key); };
  const list = o.querySelector("#wList"); let last = null;
  lib.forEach(r => {
    if (r.sec !== last) { last = r.sec; const h = document.createElement("div"); h.className = "rsec"; h.textContent = r.sec; list.appendChild(h); }
    const on = D.on.has(r.id), row = document.createElement("div"); row.className = "wex" + (on ? "" : " off");
    row.innerHTML = `<input type="checkbox" class="chk" aria-label="Include"><button class="rname"></button><input type="number" min="0" inputmode="numeric" aria-label="Target"><span class="u">${r.unit === "sec" ? "s" : "×"}</span>`;
    const c = row.querySelector(".chk"); c.checked = on;
    c.onchange = () => { c.checked ? D.on.add(r.id) : D.on.delete(r.id); drawWorkoutEditor(key); };
    const nb = row.querySelector(".rname"); nb.textContent = r.name;
    const exk = exKeyFor(r); if (exk) nb.onclick = () => openGuideFrom(exk, r, () => { openOverlay(); drawWorkoutEditor(key); }); else nb.onclick = () => { c.checked = !c.checked; c.onchange(); };
    const t = row.querySelector("input[type=number]"); t.value = D.target[r.id]; t.oninput = () => { D.target[r.id] = Math.max(0, Math.round(Number(t.value) || 0)); };
    list.appendChild(row);
  });
  o.querySelector("#wSave").onclick = () => {
    const items = lib.filter(r => D.on.has(r.id)).map(r => ({...r, target: D.target[r.id]}));
    if (!items.length) return toast("Pick at least one exercise.");
    const k = key || "w" + Date.now().toString(36);
    const areas = AREAS.filter(a => items.some(r => r.sec === a));
    const name = (D.name || "").trim() || (areas.length === 1 ? areas[0] : areas.slice(0, 3).join(" + "));
    settings.workouts = {...(settings.workouts || {}), [k]: {name, focus: areas.join(" · "), items}};
    saveSettings(); wDraft = null; drawWorkouts(); toast(`${name} saved. Choose it for any day in Your week.`);
  };
}

/* ---------- boot ---------- */
$("brandMark").innerHTML = BRAND_SVG;
$("editRoutine").onclick = () => openRoutine();
$("editWorkouts").onclick = () => openWorkouts();''')

open(P, "w", encoding="utf-8", newline="\n").write(s)
print("patched", len(s))
