"""One-off: simple. A day's workout = one or more of your saved sets (tick boxes), or Rest. Same in the week plan.
Area ticks and week templates removed. Old "areas:A|B" plans map to the saved sets with those names."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
def cut(a, b, new, include_b=False):
    global s
    i = s.index(a); j = s.index(b, i) + (len(b) if include_b else 0)
    s = s[:i] + new + s[j:]

# ---- model: "sets:a|b" = several saved sets together
rep('''const workoutKeyFor = k => { const w = (days[k] && days[k].workout) || defaultWorkoutFor(k); return workouts()[w] || (isAreaPlan(w) && planAreas(w).length) ? w : "full"; };''',
'''const isSetPlan = w => typeof w === "string" && w.startsWith("sets:");
/** The saved sets a plan entry means (old area plans → the sets you named after those areas). */
function planSets(w){
  const W = workouts();
  if (isSetPlan(w)) return w.slice(5).split("|").filter(k => W[k] && k !== "rest");
  if (isAreaPlan(w)) { const byName = Object.fromEntries(Object.keys(W).map(k => [String(W[k].name || "").toLowerCase(), k])); return planAreas(w).map(a => byName[a.toLowerCase()]).filter(Boolean); }
  return W[w] && w !== "rest" ? [w] : [];
}
const setsKey = keys => !keys.length ? "rest" : keys.length === 1 ? keys[0] : "sets:" + keys.join("|");
const workoutKeyFor = k => { const w = (days[k] && days[k].workout) || defaultWorkoutFor(k); return w === "rest" || workouts()[w] || planSets(w).length || (isAreaPlan(w) && planAreas(w).length) ? w : "full"; };''')
rep('''function resolveWorkout(key){
  const W = workouts();
  if (isAreaPlan(key)) {''', '''function resolveWorkout(key){
  const W = workouts();
  const sk = isSetPlan(key) || isAreaPlan(key) ? planSets(key) : [];
  if (sk.length) {   // several saved sets: their exercises in order, each exercise once
    const seen = new Set(), items = sk.flatMap(k => W[k].items || []).filter(r => !seen.has(r.id) && seen.add(r.id)).map(r => ({...r}));
    return {key, name: sk.map(k => W[k].name).join(" + "), focus: `${sk.length} set${sk.length > 1 ? "s" : ""} · ${items.length} exercises`, items, areas: true};
  }
  if (isAreaPlan(key)) {''')

# ---- the day's picker: tick saved sets
cut("function dayAreaPicker(k, compact){", "const WEEK_TEMPLATES = [", r'''/** Today's workout: tick one or more of your saved sets, or Rest. */
function dayAreaPicker(k, compact){
  const W = workouts(), wk = workoutKeyFor(k), plan = defaultWorkoutFor(k), chosen = planSets(wk), custom = wk !== plan;
  const box = document.createElement("div"); box.className = "dayareas" + (compact ? " compact" : "");
  box.innerHTML = `<div class="dah"><span class="fl">Workout</span><span class="dameta"></span></div><div class="chips2"></div>${custom ? `<div class="daf"><button class="linkbtn">Back to this day's plan</button></div>` : ""}`;
  const R = wk === "rest" ? null : resolveWorkout(wk);
  box.querySelector(".dameta").textContent = wk === "rest" ? "Rest day" : `${R.items.length} exercises · ~${estMin(R.items)} min`;
  const set = v => { const d = ensure(k); d.workout = v === plan ? null : v; saveDay(d, false); render(); };
  const ch = box.querySelector(".chips2");
  setKeys().filter(x => x !== "rest").forEach(key => {
    const on = chosen.includes(key), b = document.createElement("button");
    b.className = "chipbtn tick" + (on ? " on" : ""); b.setAttribute("role", "checkbox"); b.setAttribute("aria-checked", on);
    b.innerHTML = `<i>${on ? "✓" : ""}</i>${esc(W[key].name)}`;
    b.onclick = () => set(setsKey(on ? chosen.filter(x => x !== key) : [...chosen, key]));
    ch.appendChild(b);
  });
  const rb = document.createElement("button"); rb.className = "chipbtn" + (wk === "rest" ? " on" : ""); rb.textContent = "Rest"; rb.onclick = () => set("rest"); ch.appendChild(rb);
  const back = box.querySelector(".daf .linkbtn"); if (back) back.onclick = () => set(plan);
  return box;
}
''')
cut("const WEEK_TEMPLATES = [", "function repGroups(blockId, k){", "")

# ---- week plan: the same checklist per day
cut('''  const tp = document.createElement("div"); tp.className = "tpls";''', '''function drawWorkoutEditor(key){''', r'''  const note = document.createElement("p"); note.className = "beat"; note.style.margin = "4px 0"; note.textContent = "Tick the sets you train each day. Tick more than one to do them together.";
  wk.appendChild(note);
  DOW.forEach((dn, i) => {
    const e = split()[i], chosen = planSets(e);
    const r = document.createElement("div"); r.className = "wday2";
    r.innerHTML = `<div class="wdh"><b>${dn}</b><span></span></div><div class="chips2"></div>`;
    r.querySelector(".wdh span").textContent = e === "rest" || !chosen.length ? "Rest" : `${resolveWorkout(e).items.length} exercises`;
    const ch = r.querySelector(".chips2");
    const setDay = v => { const sp = [...split()]; sp[i] = v; settings.split = sp; saveSettings(); drawWorkouts(); };
    keys.forEach(k => { const on = chosen.includes(k), b = document.createElement("button"); b.className = "chipbtn tick" + (on ? " on" : "");
      b.innerHTML = `<i>${on ? "✓" : ""}</i>${esc(W[k].name)}`;
      b.onclick = () => setDay(setsKey(on ? chosen.filter(x => x !== k) : [...chosen, k])); ch.appendChild(b); });
    const rb = document.createElement("button"); rb.className = "chipbtn" + (e === "rest" || !chosen.length ? " on" : ""); rb.textContent = "Rest"; rb.onclick = () => setDay("rest"); ch.appendChild(rb);
    wk.appendChild(r);
  });
}
''')
# founder's one-time plan used the removed templates: leave the plan as it is now
rep('''      if (FOUNDERS.includes(myEmail()) && !settings.weekPlanSet) { settings.split = [...WEEK_TEMPLATES[0].plan]; settings.weekPlanSet = 1; saveSettings(); render(); }''', "")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
