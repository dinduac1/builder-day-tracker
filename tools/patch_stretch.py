"""One-off: each stretch follows the area it relaxes (biceps/triceps after upper body, calf/hip flexor after legs,
cobra after core, child's pose after back), in the routine, saved workout sets, and the set builder."""
import os, re
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, f"{s.count(a)} matches: " + a[:90]
    s = s.replace(a, b)

# --- the routine: cut the Stretch block out and put each stretch at the end of its area
i = s.index("  // ── Stretch\n"); j = s.index("];", i)
stretch = s[i:j].splitlines()[1:]
s = s[:i] + s[j:]
def take(*ids):
    out = []
    for x in ids:
        line = next(l for l in stretch if f'{{id:"{x}"' in l)
        out.append(line)
    return out
def restyle(lines, area):
    return "\n".join(l.replace('sec:"Stretch",', f'sec:"{area}", stretch:true,') for l in lines) + "\n"
up  = restyle(take("bic_str_l", "bic_str_r", "tri_str_l", "tri_str_r"), "Upper body")
leg = restyle(take("calf_str_l", "calf_str_r", "hipflex_l", "hipflex_r"), "Legs & glutes")
core = restyle(take("cobra"), "Core")
back = restyle(take("child_pose"), "Back")
rep("  // ── Legs & glutes\n", up + "  // ── Legs & glutes\n")
rep("  // ── Core\n", leg + "  // ── Core\n")
rep("  // ── Back\n", core + "  // ── Back\n")
k = s.index('  {id:"bird_dog"'); k = s.index("\n", k) + 1
s = s[:k] + back + s[k:]

# --- one label for section headers everywhere
rep("const DOW = [", '''const secLabel = r => r.sec ? r.sec + (r.stretch ? " · stretch" : "") : "";
/** Which area a stretch you wrote yourself belongs with, from its name. */
function stretchArea(name){
  const n = String(name || "").toLowerCase();
  if (/bicep|tricep|shoulder|chest|arm|wrist|neck|pec|delt/.test(n)) return "Upper body";
  if (/calf|calves|quad|hamstring|hip|glute|leg|groin|ankle|thigh|knee/.test(n)) return "Legs & glutes";
  if (/\\bab|abs|cobra|core|oblique/.test(n)) return "Core";
  if (/back|lat|spine|child|cat|cow/.test(n)) return "Back";
  return null;
}
/** Put each stretch right after the work it relaxes; items keep their own targets. */
function orderByArea(items){
  const AR = ["Upper body", "Legs & glutes", "Core", "Back"], idx = Object.fromEntries(ROUTINE.map((r, i) => [r.id, i]));
  const fixed = items.map(r => {
    const base = ROUTINE.find(x => x.id === r.id);
    if (base) return {...r, sec: base.sec, ...(base.stretch ? {stretch: true} : {})};
    if (/stretch/i.test(r.name || "") || r.sec === "Stretch") { const a = stretchArea(r.name); if (a) return {...r, sec: a, stretch: true}; }
    return r;
  });
  const rank = r => { const a = AR.indexOf(r.sec); return a < 0 ? 1e6 : a * 1e4 + (r.stretch ? 5000 : 0) + (r.id in idx ? idx[r.id] : 4999); };
  return fixed.map((r, i) => [r, i]).sort((a, b) => rank(a[0]) - rank(b[0]) || a[1] - b[1]).map(x => x[0]);
}
const DOW = [''')
rep("const PLAN_VERSION = 4;", "const PLAN_VERSION = 5;")
rep('''  if (settings.plan === PLAN_VERSION) return false;
''', '''  if (settings.plan === PLAN_VERSION) return false;
  if (settings.plan === 4) {   // v5: stretches sit with the area they relax, in every saved set
    const W = {...(settings.workouts || {})};
    Object.keys(W).forEach(k => { if (W[k] && Array.isArray(W[k].items) && k !== "rest") W[k] = {...W[k], items: orderByArea(W[k].items)}; });
    settings = {...settings, workouts: W, plan: PLAN_VERSION};
    return true;
  }
''')
# older paths end in v5 too, so run the reorder after them
rep('''    settings = {...settings, workouts: {...W, full: {...DEFAULT_WORKOUTS.full, items}, core: {...DEFAULT_WORKOUTS.core, items: []}}, plan: PLAN_VERSION};''',
    '''    settings = {...settings, workouts: {...W, full: {...DEFAULT_WORKOUTS.full, items: orderByArea(items)}, core: {...DEFAULT_WORKOUTS.core, items: []}}, plan: PLAN_VERSION};''')

# headers
rep('''        if (r.sec && r.sec !== lastSec) { lastSec = r.sec; const sh = document.createElement("div"); sh.className = "rsec"; sh.textContent = r.sec; box.appendChild(sh); }''',
    '''        if (r.sec && secLabel(r) !== lastSec) { lastSec = secLabel(r); const sh = document.createElement("div"); sh.className = "rsec"; sh.textContent = lastSec; box.appendChild(sh); }''')
rep('''sx.className = "exsec"; sx.textContent = r.sec;''', '''sx.className = "exsec"; sx.textContent = secLabel(r);''')
rep('''    if (r.sec && r.sec !== lastSec) { lastSec = r.sec; const h = document.createElement("div"); h.className = "sec"; h.textContent = r.sec; list.appendChild(h); }''',
    '''    if (r.sec && secLabel(r) !== lastSec) { lastSec = secLabel(r); const h = document.createElement("div"); h.className = "sec"; h.textContent = lastSec; list.appendChild(h); }''')

# builder: no separate Stretch area; picking an area brings its stretches
rep('''const AREAS = ["Upper body", "Legs & glutes", "Core", "Back", "Stretch", "Your own"];''', '''const AREAS = ["Upper body", "Legs & glutes", "Core", "Back", "Your own"];''')
rep('''    if (!lib.some(x => x.id === r.id) && !["mobility", "steps"].includes(r.id)) lib.push({...r, sec: r.sec || (/stretch/i.test(r.name) ? "Stretch" : "Your own")});
  }));
  return lib.sort((a, b) => AREAS.indexOf(a.sec) - AREAS.indexOf(b.sec));''', '''    if (!lib.some(x => x.id === r.id) && !["mobility", "steps"].includes(r.id)) lib.push({...r, sec: AREAS.includes(r.sec) ? r.sec : "Your own"});
  }));
  return orderByArea(lib).map(r => AREAS.includes(r.sec) ? r : {...r, sec: "Your own"});''')
rep('''    if (r.sec !== last) { last = r.sec; const h = document.createElement("div"); h.className = "rsec"; h.textContent = r.sec; list.appendChild(h); }''',
    '''    if (secLabel(r) !== last) { last = secLabel(r); const h = document.createElement("div"); h.className = "rsec"; h.textContent = last; list.appendChild(h); }''')
rep('''    const items = lib.filter(r => D.on.has(r.id)).map(r => ({...r, target: D.target[r.id]}));''',
    '''    const items = orderByArea(lib.filter(r => D.on.has(r.id)).map(r => ({...r, target: D.target[r.id]})));''')
rep("The ORDO workout trains every area: upper body, legs and glutes, core, back, then a stretch.",
    "The ORDO workout trains every area, and each area ends with the stretches that relax it.")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
