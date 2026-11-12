"""One-off: the day's workout is a checklist of areas (tick as many as you train), not a one-choice dropdown.
Used in the TRAIN block and on the workout goal row."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rep('''    const bar = document.createElement("div"); bar.className = "wsel";
    const opts = [...new Set([defaultWorkoutFor(sel), wk, ...split().filter(isAreaPlan), ...PLAN_AREAS.map(a => "areas:" + a), ...setKeys()])].filter(k => k === "rest" || W[k] || isAreaPlan(k));
    bar.innerHTML = `<label class="fl" for="wsel">Workout</label><select id="wsel" class="ed">${opts.map(k => { const R = resolveWorkout(k); return `<option value="${esc(k)}">${esc(k === "rest" ? "Rest" : R.name)}${k === defaultWorkoutFor(sel) ? " · today's plan" : ""}</option>`; }).join("")}</select>`;
    const se = bar.querySelector("select"); se.value = wk;
    se.onchange = () => { const d = ensure(sel); d.workout = se.value === defaultWorkoutFor(sel) ? null : se.value; saveDay(d,false); render(); };''',
'''    const bar = dayAreaPicker(sel);''')
rep('''      const cw = document.createElement("button"); cw.className = "linkbtn"; cw.textContent = "Workout sets";''',
    '''      if (!useSchedule()) row.appendChild(dayAreaPicker(sel, true));
      const cw = document.createElement("button"); cw.className = "linkbtn"; cw.textContent = "Workout sets";''')
rep('''const WEEK_TEMPLATES = [''', r'''/** Today's workout as a checklist: tick every area you're training (one, two, all of them). Saved sets and Rest too. */
function dayAreaPicker(k, compact){
  const W = workouts(), wk = workoutKeyFor(k), plan = defaultWorkoutFor(k), areas = planAreas(wk);
  const box = document.createElement("div"); box.className = "dayareas" + (compact ? " compact" : "");
  const custom = wk !== plan;
  box.innerHTML = `<div class="dah"><span class="fl">Train today</span><span class="dameta"></span></div><div class="chips2"></div>
    <div class="daf"><select class="wset" aria-label="Or a saved set"><option value="">Or a saved set…</option>${setKeys().filter(x => x !== "rest").map(x => `<option value="${esc(x)}">${esc(W[x].name)}</option>`).join("")}</select>${custom ? `<button class="linkbtn">Back to this day's plan</button>` : ""}</div>`;
  const R = wk === "rest" ? null : resolveWorkout(wk);
  box.querySelector(".dameta").textContent = wk === "rest" ? "Rest day" : `${R.items.length} exercises · ~${estMin(R.items)} min${custom ? " · changed for today" : ""}`;
  const set = v => { const d = ensure(k); d.workout = v === plan ? null : v; saveDay(d, false); render(); };
  const ch = box.querySelector(".chips2");
  PLAN_AREAS.forEach(a => {
    const on = areas.includes(a), b = document.createElement("button");
    b.className = "chipbtn tick" + (on ? " on" : ""); b.setAttribute("role", "checkbox"); b.setAttribute("aria-checked", on);
    b.innerHTML = `<i>${on ? "✓" : ""}</i>${esc(a)}`;
    b.onclick = () => set(areaPlanKey(on ? areas.filter(x => x !== a) : [...areas, a]));
    ch.appendChild(b);
  });
  const rb = document.createElement("button"); rb.className = "chipbtn" + (wk === "rest" ? " on" : ""); rb.textContent = "Rest"; rb.onclick = () => set("rest"); ch.appendChild(rb);
  const se = box.querySelector(".wset"); se.value = W[wk] && wk !== "rest" ? wk : "";
  se.onchange = () => { if (se.value) set(se.value); };
  const back = box.querySelector(".daf .linkbtn"); if (back) back.onclick = () => set(plan);
  return box;
}
const WEEK_TEMPLATES = [''')
rep("</style>\n</head>", """.dayareas{display:grid;gap:8px;margin:4px 0 6px}
.dayareas .dah{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.dayareas .dameta{font-size:12px;color:var(--muted)}
.dayareas .daf{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center}
.dayareas .wset{font:inherit;font-size:13px;padding:7px 10px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--muted)}
.chipbtn.tick{display:inline-flex;align-items:center;gap:7px}
.chipbtn.tick i{width:16px;height:16px;border-radius:5px;border:1.5px solid var(--line-strong);display:grid;place-content:center;font-style:normal;font-size:11px;line-height:1}
.chipbtn.tick.on i{border-color:var(--accent-ink);background:var(--accent-ink);color:var(--accent)}
.goal .dayareas{grid-column:2 / -1}
</style>
</head>""")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
