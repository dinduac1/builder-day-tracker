"""One-off upgrade of index.html to ORDO: new design system, hero, goals + challenges (75 Hard),
crew leaderboard, share sheet, onboarding/settings, and the rebalanced workout. Run once."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..", "index.html")
s = open(P, encoding="utf-8").read()
assert "ORDO" not in s[:3000], "already patched"

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n >= count, (n, old[:100])
    s = s.replace(old, new, count)

def between(start, end):
    a = s.index(start); b = s.index(end, a)
    return a, b

# =============================================================== head
rep('<meta name="theme-color" content="#123a26">', '<meta name="theme-color" content="#08090C">')
rep('<meta name="apple-mobile-web-app-title" content="Builder Day">', '<meta name="apple-mobile-web-app-title" content="ORDO">')
rep('''<meta name="description" content="Daily tracker for the Full-Time Builder Day: wake time, time per block, reps, records, the Daily Five and a weekly grade.">''',
    '''<meta name="description" content="ORDO: daily goals, challenges like 75 Hard, guided workouts, grades and a crew that keeps you honest.">''')
a, b = between('<link rel="icon" href="data:image/svg+xml', '\n')
s = s[:a] + '<link rel="icon" type="image/png" href="favicon.png">' + s[b:]
rep('<title>Builder Day Tracker</title>', '<title>ORDO</title>')
rep('family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Public+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;600',
    'family=Big+Shoulders+Display:wght@600;700;800&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600')
a, b = between("<style>\n", "</style>")
s = s[:a] + "<style>\n" + open(os.path.join(HERE, "ordo.css"), encoding="utf-8").read() + s[b:]
# apply the saved theme before first paint
rep('<link rel="preconnect" href="https://fonts.googleapis.com">',
    '''<script>try{var t=localStorage.getItem("ordo-theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t)}catch(e){}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">''')

# =============================================================== page skeleton
a, b = between('<div class="wrap">\n  <header class="top">', '  <div class="ovl" id="ovl" hidden></div>')
s = s[:a] + '''<div class="wrap">
  <header class="top">
    <div class="brand"><span id="brandMark"></span><span class="word">ORDO</span></div>
    <div class="hdr-right">
      <div class="datenav">
        <button id="prev" aria-label="Previous day">←</button>
        <div class="dlabel" id="dlabel">—</div>
        <button id="next" aria-label="Next day">→</button>
        <button id="today">Today</button>
      </div>
      <button class="iconbtn" id="settingsBtn" aria-label="Settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/></svg></button>
    </div>
  </header>

  <section class="hero" id="hero">
    <div>
      <div class="hi" id="heroDate"></div>
      <h1 id="heroHi">Discipline, kept.</h1>
      <div class="chips" id="heroChips"></div>
      <div class="store-note" id="storeNote" style="color:rgba(243,241,236,.55);margin-top:10px">Loading…</div>
      <div class="auth" id="auth"></div>
      <button class="linkbtn" id="remindLink" hidden>Turn on reminders</button>
    </div>
    <div class="ringwrap" id="heroRing"></div>
  </section>

  <div class="now" id="nowbar"></div>
  <div class="grid">
    <div class="main">
      <section class="panel p-goals" id="goalsPanel">
        <div class="phead"><h2 id="goalsTitle">Today's goals</h2><span class="meta" id="goalsMeta"></span></div>
        <div class="goals" id="goals"></div>
      </section>
      <section class="panel p-sched">
        <div class="phead"><h2>Schedule</h2><span class="meta" id="blockMeta">0 / 14 blocks</span></div>
        <ul class="tl" id="tl"></ul>
      </section>
      <section class="panel p-review" id="reviewPanel">
        <div class="phead"><h2>Evening review</h2><span class="meta">tonight</span></div>
        <div class="revbody" id="review"></div>
      </section>
    </div>
    <aside class="side">
      <section class="panel p-five">
        <div class="phead"><h2>The Five</h2><span class="meta">never miss twice</span></div>
        <div class="fivegrid" id="fivegrid"></div>
        <div class="score">
          <div class="big" id="fiveScore">0<small>/5</small></div>
          <div class="streak">Full-Five streak<b id="streak">0 days</b></div>
        </div>
        <div class="alerts" id="alerts"></div>
      </section>
      <section class="panel p-day">
        <div class="phead"><h2>Daily score</h2><span class="meta" id="dayLabel">today</span></div>
        <div class="wk" id="dayScore"></div>
      </section>
      <section class="panel p-crew" id="crewPanel" hidden>
        <div class="phead"><h2>Crew</h2><span class="meta" id="crewMeta"></span></div>
        <div class="crew" id="crew"></div>
      </section>
      <section class="panel p-acct">
        <div class="phead"><h2>Accountability</h2><span class="meta" id="acctMeta">stakes</span></div>
        <div class="acct" id="acct"></div>
      </section>
      <section class="panel p-plan">
        <div class="phead"><h2>Today's top 3</h2><span class="meta">set last night</span></div>
        <div class="plan" id="plan"></div>
      </section>
      <section class="panel p-week">
        <div class="phead"><h2>Weekly score</h2><span class="meta" id="wkLabel">Mon–Sun</span></div>
        <div class="wk" id="wk"></div>
      </section>
      <section class="panel p-heat">
        <div class="phead"><h2>Last 12 weeks</h2><span class="meta">Five per day</span></div>
        <div class="heatwrap">
          <div class="heat" id="heat"></div>
          <div class="legend">0 <i style="background:var(--heat0)"></i><i style="background:var(--heat1)"></i><i style="background:var(--heat2)"></i><i style="background:var(--heat3)"></i><i style="background:var(--heat4)"></i><i style="background:var(--heat5)"></i> 5</div>
          <div class="stats">
            <div><b id="stBest">0</b><span>Best streak</span></div>
            <div><b id="stFull">0</b><span>Full-Five days</span></div>
            <div><b id="stAvg">0</b><span>Avg Five / day (30d)</span></div>
          </div>
        </div>
      </section>
      <section class="panel p-remind" id="remindPanel" hidden>
        <div class="phead"><h2>Reminders</h2><span class="meta">on this device</span></div>
        <div class="remind" id="remind"></div>
      </section>
    </aside>
  </div>
''' + s[b:]
rep('<p class="rule">Excellence is a sleep-powered game.</p>', '<p class="rule">ORDO · Discipline, kept.</p>')

# =============================================================== workout: rebalanced routine
EX_NEW = r'''
  flutter:  {name:"Flutter Kicks", video:"bfMYh_-o8qA", muscles:["Lower abs","Hip flexors"],
             steps:["Lie on your back, hands under your hips, lower back pressed into the floor.","Lift both straight legs a few inches off the floor.","Kick them up and down in small, quick alternating strokes.","Keep breathing and keep the lower back down the whole time."],
             mistakes:["Lower back arching off the floor","Bending the knees","Kicking too high so the abs switch off"]},
  revcrunch:{name:"Reverse Crunch", video:"5HyXYi1oqZE", muscles:["Lower abs"],
             steps:["Lie on your back, knees bent at 90° above your hips, arms by your sides.","Curl your hips off the floor, bringing your knees toward your chest.","Pause, then lower slowly until your hips touch down.","Move from the abs, not by swinging the legs."],
             mistakes:["Using momentum","Dropping the hips fast","Pushing hard through the hands"]},
  ankletap: {name:"Ankle Taps", video:"RzaD0I3yeKY", muscles:["Obliques","Abs"],
             steps:["Lie on your back, knees bent, feet flat and a little wider than hips.","Lift your head and shoulders off the floor.","Reach side to side, tapping each hand to the same-side ankle.","Keep the shoulders up the whole set."],
             mistakes:["Dropping the head between taps","Pulling on the neck","Rushing with tiny reaches"]},
  bicycle:  {name:"Bicycle Crunch", video:"VaL7XWK3MVE", muscles:["Obliques","Abs"],
             steps:["Lie on your back, hands lightly behind your head, shoulders lifted.","Bring one knee in while the other leg extends.","Rotate to bring the opposite elbow toward the bent knee.","Switch sides in a slow, controlled pedal."],
             mistakes:["Yanking the neck","Racing through it","Letting the lower back lift"]},
  climber:  {name:"Mountain Climbers", video:"re3dtmzGCOc", muscles:["Core","Shoulders","Hip flexors"],
             steps:["Start in a high plank, hands under shoulders.","Drive one knee toward your chest, then switch legs quickly.","Keep your hips level with your shoulders.","Breathe and keep a steady rhythm."],
             mistakes:["Hips piking up","Bouncing the hips","Hands drifting in front of the shoulders"]},
  deadbug:  {name:"Dead Bug", video:"xtTIb6dC-vI", muscles:["Deep core","Abs"],
             steps:["Lie on your back, arms straight up, knees bent at 90° above your hips.","Press your lower back into the floor.","Slowly lower one arm and the opposite leg toward the floor.","Return and switch sides without letting the back arch."],
             mistakes:["Lower back lifting","Moving too fast","Holding your breath"]},
  sumo:     {name:"Sumo Squat", video:"ksmxuw3JDbQ", muscles:["Inner thighs","Glutes","Quads"],
             steps:["Feet wide, toes turned out about 30–45°.","Push your hips back and down, knees tracking over your toes.","Lower until your thighs are about parallel.","Drive through your heels and squeeze your glutes to stand."],
             mistakes:["Knees caving in","Chest dropping forward","Heels lifting"]},
  sidelunge:{name:"Side Lunges", video:"apsp_uuXZTU", muscles:["Inner thighs","Glutes","Quads"],
             steps:["Stand with feet together.","Take a big step to one side and sit your hips back over that foot, other leg straight.","Keep your chest up and the bent knee over the toes.","Push off the heel back to the start; alternate sides."],
             mistakes:["Knee collapsing inward","Rounding the back","Heel lifting off"]},
  bulgarian:{name:"Bulgarian Split Squat", video:"YFLHDXeekVc", muscles:["Quads","Glutes"],
             steps:["Stand a stride in front of a bench, rear foot laces-down on it.","Lower straight down until the back knee nearly touches the floor.","Keep most of your weight on the front leg, torso tall or slightly forward.","Drive up through the front heel."],
             mistakes:["Front foot too close to the bench","Pushing off the back foot","Front knee caving in"]},
  kickback: {name:"Glute Kickbacks", video:"KEaLf6QraWU", muscles:["Glutes","Hamstrings"],
             steps:["On all fours, hands under shoulders, knees under hips.","Keeping the knee bent at 90°, drive one foot up toward the ceiling.","Squeeze the glute at the top without arching your back.","Lower with control; alternate or do all reps one side."],
             mistakes:["Arching the lower back","Swinging the leg","Twisting the hips open"]},
  wallsit:  {name:"Wall Sit", video:"cWTZ8Am1Ee0", muscles:["Quads","Glutes"],
             steps:["Stand with your back against a wall, feet about two feet out.","Slide down until your knees are at 90°.","Keep your back flat on the wall and knees over ankles.","Hold, breathing steadily."],
             mistakes:["Knees past the toes","Sitting too high","Hands pushing on the thighs"]},
  superman: {name:"Superman", video:"z6PJMT2y8GQ", muscles:["Lower back","Glutes","Upper back"],
             steps:["Lie face down, arms straight out in front.","Squeeze your glutes and lift arms, chest and legs a few inches off the floor.","Hold for a second at the top, looking at the floor.","Lower slowly and repeat."],
             mistakes:["Cranking the neck up","Lifting too high and pinching the back","Rushing"]},
  birddog:  {name:"Bird Dog", video:"ZdAHe9_HeEw", muscles:["Lower back","Core","Glutes"],
             steps:["On all fours, hands under shoulders, knees under hips, back flat.","Reach one arm forward and the opposite leg back until both are level with your body.","Hold for two seconds without rotating the hips.","Return and switch sides."],
             mistakes:["Hips rotating open","Arching the back","Moving too fast"]},
  hipflexor:{name:"Hip Flexor Stretch", video:"K5EZ8ztNEcw", muscles:["Hip flexors","Quads"],
             steps:["Kneel on one knee, the other foot flat in front.","Tuck your pelvis under and squeeze the back glute.","Shift your hips forward until you feel the front of the back hip stretch.","Stay tall and breathe; hold."],
             mistakes:["Arching the lower back","Leaning the torso forward"]},
  childpose:{name:"Child's Pose", video:"_ZX_zTOBgp8", muscles:["Lower back","Hips","Lats"],
             steps:["Kneel, toes together, knees about hip-width.","Sit back toward your heels.","Fold forward, arms reaching long in front, forehead down.","Let your back and shoulders relax; breathe slowly."],
             mistakes:["Forcing the hips down","Holding tension in the shoulders"]},
};'''
rep('''  cobra:    {name:"Cobra Stretch",''', '''  __COBRA__''')
a = s.index('  __COBRA__'); b = s.index('};', a) + 2
cobra_def = s[a:b].replace('  __COBRA__', '  cobra:    {name:"Cobra Stretch",', 1)
s = s[:a] + cobra_def[:-2].rstrip().rstrip(',') + ',' + EX_NEW[1:].replace('\n};', '\n};', 1) + s[b:]

a, b = between('const ROUTINE = [', '];\n')
s = s[:a] + r'''const ROUTINE = [
  // ── Upper body
  {id:"wide_pushups", ex:"wide",       sec:"Upper body", name:"Wide Arm Push-Ups",               target:30},
  {id:"row_left",     ex:"row",        sec:"Upper body", name:"Bent Over Dumbbell Rows · left",  target:30},
  {id:"row_right",    ex:"row",        sec:"Upper body", name:"Bent Over Dumbbell Rows · right", target:30},
  {id:"military",     ex:"press",      sec:"Upper body", name:"Military Press",                  target:30},
  {id:"pushups",      ex:"pushup",     sec:"Upper body", name:"Push-Ups",                        target:30},
  {id:"lateral",      ex:"lateral",    sec:"Upper body", name:"Dumbbell Side Lateral Raise",     target:30},
  {id:"dips",         ex:"dips",       sec:"Upper body", name:"Triceps Dips",                    target:30},
  {id:"hammer",       ex:"hammer",     sec:"Upper body", name:"Alternate Hammer Curl",           target:30},
  {id:"diamond",      ex:"diamond",    sec:"Upper body", name:"Diamond Push-Ups",                target:30},
  {id:"decline",      ex:"decline",    sec:"Upper body", name:"Decline Push-Ups",                target:30},
  // ── Legs & glutes
  {id:"squats",       ex:"squat",      sec:"Legs & glutes", name:"Squats",                       target:30},
  {id:"sumo",         ex:"sumo",       sec:"Legs & glutes", name:"Sumo Squat",                   target:20},
  {id:"lunges",       ex:"lunges",     sec:"Legs & glutes", name:"Lunges",                       target:20},
  {id:"side_lunges",  ex:"sidelunge",  sec:"Legs & glutes", name:"Side Lunges",                  target:20},
  {id:"bulg_left",    ex:"bulgarian",  sec:"Legs & glutes", name:"Bulgarian Split Squat · left", target:12},
  {id:"bulg_right",   ex:"bulgarian",  sec:"Legs & glutes", name:"Bulgarian Split Squat · right",target:12},
  {id:"hip_hinge",    ex:"hinge",      sec:"Legs & glutes", name:"Hip Hinge",                    target:30},
  {id:"kickbacks",    ex:"kickback",   sec:"Legs & glutes", name:"Glute Kickbacks",              target:20},
  {id:"calves",       ex:"calf",       sec:"Legs & glutes", name:"Calf Raises",                  target:30},
  {id:"wall_sit",     ex:"wallsit",    sec:"Legs & glutes", name:"Wall Sit",                     target:60, unit:"sec"},
  {id:"bridge_hold",  ex:"bridge",     sec:"Legs & glutes", name:"Bridge (hold)",                target:180, unit:"sec"},
  // ── Core
  {id:"situps",       ex:"situps",     sec:"Core", name:"Sit-Ups",                               target:10},
  {id:"legraise",     ex:"legraise",   sec:"Core", name:"Leg Raises",                            target:10},
  {id:"flutter",      ex:"flutter",    sec:"Core", name:"Flutter Kicks",                         target:45, unit:"sec"},
  {id:"rev_crunch",   ex:"revcrunch",  sec:"Core", name:"Reverse Crunch",                        target:45, unit:"sec"},
  {id:"ankle_taps",   ex:"ankletap",   sec:"Core", name:"Ankle Taps",                            target:45, unit:"sec"},
  {id:"bicycle",      ex:"bicycle",    sec:"Core", name:"Bicycle Crunch",                        target:45, unit:"sec"},
  {id:"climbers",     ex:"climber",    sec:"Core", name:"Mountain Climbers",                     target:45, unit:"sec"},
  {id:"dead_bug",     ex:"deadbug",    sec:"Core", name:"Dead Bug",                              target:45, unit:"sec"},
  {id:"plank",        ex:"plank",      sec:"Core", name:"Plank",                                 target:120, unit:"sec"},
  {id:"side_plank_r", ex:"sideplank",  sec:"Core", name:"Side Plank · right",                    target:60, unit:"sec"},
  {id:"side_plank_l", ex:"sideplank",  sec:"Core", name:"Side Plank · left",                     target:60, unit:"sec"},
  // ── Back
  {id:"superman",     ex:"superman",   sec:"Back", name:"Superman",                              target:20},
  {id:"bird_dog",     ex:"birddog",    sec:"Back", name:"Bird Dog",                              target:20},
  // ── Stretch
  {id:"bic_str_l",    ex:"bicstretch", sec:"Stretch", name:"Standing Biceps Stretch · left",     target:30, unit:"sec"},
  {id:"bic_str_r",    ex:"bicstretch", sec:"Stretch", name:"Standing Biceps Stretch · right",    target:30, unit:"sec"},
  {id:"tri_str_l",    ex:"tristretch", sec:"Stretch", name:"Triceps Stretch · left",             target:60, unit:"sec"},
  {id:"tri_str_r",    ex:"tristretch", sec:"Stretch", name:"Triceps Stretch · right",            target:60, unit:"sec"},
  {id:"calf_str_l",   ex:"calfstretch",sec:"Stretch", name:"Calf Stretch · left",                target:20, unit:"sec"},
  {id:"calf_str_r",   ex:"calfstretch",sec:"Stretch", name:"Calf Stretch · right",               target:20, unit:"sec"},
  {id:"hipflex_l",    ex:"hipflexor",  sec:"Stretch", name:"Hip Flexor Stretch · left",          target:30, unit:"sec"},
  {id:"hipflex_r",    ex:"hipflexor",  sec:"Stretch", name:"Hip Flexor Stretch · right",         target:30, unit:"sec"},
  {id:"cobra",        ex:"cobra",      sec:"Stretch", name:"Cobra Stretch",                      target:60, unit:"sec"},
  {id:"child_pose",   ex:"childpose",  sec:"Stretch", name:"Child's Pose",                       target:60, unit:"sec"},
''' + s[b:]
rep('focus:"FULL BODY TRAIN 10 · stretches included"', 'focus:"Upper · legs · core · back · stretch"')
rep('const PLAN_VERSION = 3;', 'const PLAN_VERSION = 4;')
# v3 -> v4: swap in the balanced routine, keeping your own target changes and any counters you added
rep('''function migratePlan(){
  if (settings.plan === PLAN_VERSION) return false;''', '''function migratePlan(){
  if (settings.plan === PLAN_VERSION) return false;
  if (settings.plan === 3) {
    const W = settings.workouts || {}, old = (W.full || {}).items || [];
    const byId = Object.fromEntries(old.map(r => [r.id, r]));
    const items = ROUTINE.map(r => byId[r.id] ? {...r, target: byId[r.id].target || r.target} : {...r});
    old.filter(r => !ROUTINE.some(x => x.id === r.id)).forEach(r => items.push(r));
    settings = {...settings, workouts: {...W, full: {...DEFAULT_WORKOUTS.full, items}, core: {...DEFAULT_WORKOUTS.core, items: []}}, plan: PLAN_VERSION};
    return true;
  }''')
# older paths jump straight to v4 by running the v2->v3 step first
rep('''  if (settings.plan === 2) {''', '''  if (settings.plan === 2 || settings.plan === undefined && false) {''')

# section labels inside the TRAIN counters and the player
rep('''      g.items.forEach(r => {
        const v = day.reps[r.id], has = v != null, n = v || 0;''', '''      let lastSec = null;
      g.items.forEach(r => {
        if (r.sec && r.sec !== lastSec) { lastSec = r.sec; const sh = document.createElement("div"); sh.className = "rsec"; sh.textContent = r.sec; box.appendChild(sh); }
        const v = day.reps[r.id], has = v != null, n = v || 0;''')
rep('''  o.querySelector(".exname").textContent = r.name;''', '''  o.querySelector(".exname").textContent = r.name;
  if (r.sec) { const sx = document.createElement("div"); sx.className = "exsec"; sx.textContent = r.sec; o.querySelector(".exname").before(sx); }''')
rep('''  player.items.forEach((r, idx) => {
    const v = player.log[r.id], b = document.createElement("button");''', '''  let lastSec = null;
  player.items.forEach((r, idx) => {
    if (r.sec && r.sec !== lastSec) { lastSec = r.sec; const h = document.createElement("div"); h.className = "sec"; h.textContent = r.sec; list.appendChild(h); }
    const v = player.log[r.id], b = document.createElement("button");''')

# a guided workout started from a goal also fills that goal's minutes
rep('''  if (JSON.stringify(session) !== JSON.stringify(d.session || null)) { d.session = session; changed = true; }''',
    '''  if (JSON.stringify(session) !== JSON.stringify(d.session || null)) { d.session = session; changed = true; }
  if (player.goalId && mins > 0) {
    const cur = (d.goals || {})[player.goalId] || 0;
    if (mins > cur) { d.goals = {...(d.goals || {}), [player.goalId]: mins}; changed = true; }
  }''')
rep('''function startWorkout(items){''', '''let pendingGoalId = null;   // set when a workout is started from a goal
function startWorkout(items){''')
rep('''function beginWorkout(items, resume, fresh){
  blockStarted("train");''', '''function beginWorkout(items, resume, fresh){
  blockStarted("train");
  const goalId = pendingGoalId; pendingGoalId = null;''')
rep('''    savedLog: {}, savedMins: 0, activeMs: 0, segStart: Date.now(), autoDone: false, finished: false});''',
    '''    savedLog: {}, savedMins: 0, activeMs: 0, segStart: Date.now(), autoDone: false, finished: false, goalId});''')

# =============================================================== data helpers
rep('''const hasData = d => d && (doneCount(d) > 0 ||''', '''const hasData = d => d && (Object.values(d.goals || {}).some(v => v) || doneCount(d) > 0 ||''')

# =============================================================== scoring: goals join the daily + weekly grade
rep('''function scoreDay(k){
  const today = keyOf(new Date()), fk = firstKey(), d = getDay(k);
  if (k > today || (!hasData(days[k]) && k !== today)) return null;''', '''function scoreDay(k){
  const today = keyOf(new Date()), fk = firstKey(), d = getDay(k);
  if (k > today || (!hasData(days[k]) && k !== today)) return null;
  const G = goalsList();
  if (!useSchedule()) {
    if (!G.length) return null;
    const g = goalProgress(k);
    const parts = [{label:"Goals done", max:100, frac:g.frac, note:`${g.done}/${g.total}`}];
    const score = Math.round(g.frac * 100);
    return {score, grade: gradeOf(score), parts, live: k === today};
  }''')
rep('''    {label:"Never missed twice", max:10, frac:1 - doubles / 5, note:doubles ? `${doubles} missed two days running` : "clean"},
  ];
  const live = parts.filter(p => p.frac != null);
  const score = Math.round(live.reduce((t, p) => t + p.max * p.frac, 0) / live.reduce((t, p) => t + p.max, 0) * 100);
  return {score, grade: gradeOf(score), parts, live: k === today};''', '''    {label:"Never missed twice", max:10, frac:1 - doubles / 5, note:doubles ? `${doubles} missed two days running` : "clean"},
  ];
  if (G.length) { const g = goalProgress(k); parts.unshift({label:"Goals done", max:40, frac:g.frac, note:`${g.done}/${g.total}`}); }
  const live = parts.filter(p => p.frac != null);
  const score = Math.round(live.reduce((t, p) => t + p.max * p.frac, 0) / live.reduce((t, p) => t + p.max, 0) * 100);
  return {score, grade: gradeOf(score), parts, live: k === today};''')
rep('''function scoreWeek(ws, withRecords){
  const today = keyOf(new Date()), fk = firstKey();
  const keys = [0,1,2,3,4,5,6].map(i => shift(ws,i));
  const scorable = keys.filter(k => fk && k >= fk && k < today);  // today counts once it's over
  if (!scorable.length) return null;''', '''function scoreWeek(ws, withRecords){
  const today = keyOf(new Date()), fk = firstKey();
  const keys = [0,1,2,3,4,5,6].map(i => shift(ws,i));
  const scorable = keys.filter(k => fk && k >= fk && k < today);  // today counts once it's over
  if (!scorable.length) return null;
  const G = goalsList();
  const goalFrac = G.length ? scorable.reduce((t, k) => t + goalProgress(k).frac, 0) / scorable.length : null;
  if (!useSchedule()) {
    if (goalFrac == null) return null;
    const full = scorable.filter(k => goalProgress(k).frac >= 1).length;
    const score = Math.round(goalFrac * 100);
    return {score, grade: gradeOf(score), n: scorable.length, final: keys[6] < today, keys, records: 0,
      parts: [{label:"Goals done", max:100, frac:goalFrac, note:`${full}/${scorable.length} full days`}]};
  }''')
rep('''    {label:"Never missed twice", max:10, frac:Math.max(0, 1 - doubles/5), note:doubles ? `${doubles} double miss${doubles>1?"es":""}` : "clean"},
  ];''', '''    {label:"Never missed twice", max:10, frac:Math.max(0, 1 - doubles/5), note:doubles ? `${doubles} double miss${doubles>1?"es":""}` : "clean"},
  ];
  if (goalFrac != null) parts.unshift({label:"Goals done", max:40, frac:goalFrac, note:`${Math.round(goalFrac * 100)}% average`});''')

# stakes: schedule rules only apply with the schedule; strict challenges add their own
rep('''  const twice = FIVE.filter(f => !d.done[f] && !y.done[f] && (hasData(days[shift(k, -1)]) || k > a.start));
  if (twice.length) out.push(`Missed twice: ${twice.map(f => SHORT[f]).join(", ")}`);
  return out;''', '''  if (useSchedule()) {
    const twice = FIVE.filter(f => !d.done[f] && !y.done[f] && (hasData(days[shift(k, -1)]) || k > a.start));
    if (twice.length) out.push(`Missed twice: ${twice.map(f => SHORT[f]).join(", ")}`);
  }
  const c = settings.challenge;
  if (c && c.start && k >= c.start && goalsList().length && goalProgress(k).frac < 1) out.push(`Missed a ${c.name} goal`);
  return out;''')
rep('''    box.innerHTML = `<p class="beat">Put money on the line. Every finished day below your grade bar, with one of the Five missed two days running, or not tracked at all, adds your stake to what you owe. Your accountability partner holds you to paying it.</p>`;''',
    '''    box.innerHTML = `<p class="beat">Put money on the line. Every finished day below your grade bar, with a goal missed, or not tracked at all, adds your stake to what you owe. Your accountability partner holds you to paying it.</p>`;''')

# =============================================================== report: elite text + share sheet
a, b = between('function reportText(k){', '/* ---------- evening reflection ---------- */')
s = s[:a] + r'''/** The day report. style: "wa" (WhatsApp bold), "plain" (Telegram, email, other apps), "sms" (compact). */
function reportText(k, style = "plain"){
  const d = getDay(k), sc = scoreDay(k), ys = scoreDay(shift(k, -1)), a = acct();
  const L = a.start ? stakeLedger(keyOf(new Date())) : null, cs = challengeState(keyOf(new Date()));
  const B = t => style === "wa" ? `*${t}*` : t;
  const tick = ok => ok ? "✓" : "✗";
  const date = fromKey(k).toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short", year: "numeric"});
  const name = (profile().name || "").trim();
  const out = [];
  const head = [];
  head.push(B("ORDO · DAY REPORT") + (name ? `  ${name}` : ""));
  head.push(date + (cs ? `  ·  ${cs.name.toUpperCase()} DAY ${cs.dayN}/${cs.length}` : ""));
  out.push(head.join("\n"));
  if (sc) {
    let line = `${B("GRADE")}  ${sc.grade} · ${sc.score}/100`;
    if (ys) line += sc.score > ys.score ? `  ▲ from ${ys.grade}` : sc.score < ys.score ? `  ▼ from ${ys.grade}` : `  = ${ys.grade}`;
    out.push(line);
  }
  const G = goalsList();
  if (G.length) {
    const g = goalProgress(k);
    const rows = G.map(goal => {
      const v = (d.goals || {})[goal.id];
      const ok = goalDone(goal, v);
      const amt = goal.type === "check" ? "" : `  ${fmtGoal(goal, v || 0)}/${fmtGoal(goal, goal.target)}${goal.unit ? " " + goal.unit : ""}`;
      return `${tick(ok)} ${goal.name}${style === "sms" ? "" : amt}`;
    });
    out.push(`${B("GOALS")}  ${g.done}/${g.total}\n` + rows.join("\n"));
  }
  if (useSchedule()) {
    out.push(`${B("THE FIVE")}  ${fiveCount(d)}/5\n` + FIVE.map(f => `${tick(d.done[f])} ${SHORT[f]}`).join("   "));
    if (style !== "sms") {
      const trainReps = repDefs("train", k).filter(r => r.unit !== "sec").reduce((t, r) => t + (repOf(k, r.id) || 0), 0);
      const trainMin = minsOf(k, "train");
      if (trainReps || trainMin) out.push(`${B("TRAINING")}  ${trainReps ? trainReps.toLocaleString() + " reps" : ""}${trainReps && trainMin ? " · " : ""}${trainMin ? trainMin + " min" : ""}`);
      out.push(`${B("BLOCKS")}  ${doneCount(d)}/${BLOCKS.length}`);
    }
  }
  const refl = [];
  if (d.proud) refl.push(`${B("WIN")}       ${d.proud}`);
  if (d.notProud && style !== "sms") refl.push(`${B("LESSON")}    ${d.notProud}`);
  if (d.doDiff) refl.push(`${B("TOMORROW")}  ${d.doDiff}`);
  if (refl.length) out.push(refl.join("\n"));
  const top = (d.top3 || []).filter(Boolean);
  if (top.length && style !== "sms") out.push(`${B("TOP 3 FOR TOMORROW")}\n` + top.map((t, i) => `${i + 1}. ${t}`).join("\n"));
  if (L) out.push(L.owed ? `${B("STAKES")}  ${naira(L.owed)} owed (${L.debts.length} day${L.debts.length > 1 ? "s" : ""}). Hold me to it.` : `${B("STAKES")}  All clear.`);
  return out.join("\n\n");
}
const SHARE_ICONS = {
  wa: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.2c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2.1 1-2.4c.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5l.8 2c.1.2.1.4 0 .5l-.3.5-.4.5c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.7-.1l1.9.9c.3.1.5.2.5.3.1.2.1.7-.1 1.3z"/></svg>',
  tg: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.9 4.6 18.8 19c-.2 1-.8 1.3-1.7.8l-4.6-3.4-2.2 2.1c-.2.2-.5.5-1 .5l.3-4.7 8.6-7.8c.4-.3-.1-.5-.6-.2L7 13l-4.6-1.4c-1-.3-1-1 .2-1.5l17.9-6.9c.8-.3 1.6.2 1.4 1.4z"/></svg>',
  sms: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg>',
  mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/></svg>',
  more: '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>',
  send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/></svg>',
};
function openShare(k){
  const a = acct(), site = location.origin + location.pathname;
  const sh = document.createElement("div"); sh.className = "sheet";
  sh.innerHTML = `<div class="card" role="dialog" aria-label="Send your report">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h3>Send your report</h3><button class="btn" data-x>Close</button></div>
    <pre></pre>
    <div class="apps"></div>
    <p class="beat" id="shareNote"></p></div>`;
  sh.querySelector("pre").textContent = reportText(k, "plain");
  const apps = sh.querySelector(".apps");
  const add = (label, color, icon, href, onclick) => {
    const el = document.createElement(href ? "a" : "button");
    if (href) { el.href = href; el.target = "_blank"; el.rel = "noopener"; }
    el.innerHTML = `<span class="ic" style="background:${color}">${SHARE_ICONS[icon]}</span><span>${label}</span>`;
    if (onclick) el.onclick = onclick;
    apps.appendChild(el);
  };
  const phone = a.partner ? a.partner.replace(/[^0-9]/g, "") : "";
  add("WhatsApp", "#25D366", "wa", `https://api.whatsapp.com/send?${phone ? "phone=" + phone + "&" : ""}text=${encodeURIComponent(reportText(k, "wa"))}`);
  add("Telegram", "#2AABEE", "tg", `https://t.me/share/url?url=${encodeURIComponent(site)}&text=${encodeURIComponent(reportText(k, "plain"))}`);
  add("SMS", "#4B5563", "sms", `sms:${phone ? "+" + phone : ""}?body=${encodeURIComponent(reportText(k, "sms"))}`);
  add("Email", "#3B4CE0", "mail", `mailto:?subject=${encodeURIComponent("ORDO day report · " + fromKey(k).toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short"}))}&body=${encodeURIComponent(reportText(k, "plain"))}`);
  add("Copy", "#111318", "copy", null, async () => {
    try { await navigator.clipboard.writeText(reportText(k, "plain")); sh.querySelector("#shareNote").textContent = "Copied. Paste it anywhere."; }
    catch(e) { const r = document.createRange(); r.selectNodeContents(sh.querySelector("pre")); getSelection().removeAllRanges(); getSelection().addRange(r); sh.querySelector("#shareNote").textContent = "Selected. Copy it from your keyboard menu."; }
  });
  if ((NATIVE && NATIVE.share) || navigator.share) add("Other apps", "#6B7280", "more", null, () => {
    const txt = reportText(k, "plain");
    if (NATIVE && NATIVE.share) NATIVE.share(txt, "ORDO day report");
    else navigator.share({text: txt}).catch(() => {});
  });
  sh.onclick = e => { if (e.target === sh || e.target.hasAttribute("data-x")) sh.remove(); };
  document.body.appendChild(sh);
}
function reportButton(k){
  const btn = document.createElement("button"); btn.className = "sendrep";
  btn.innerHTML = SHARE_ICONS.send + "<span>Send tonight's report</span>";
  btn.onclick = () => openShare(k);
  return btn;
}

''' + s[b:]

# =============================================================== profile, goals, challenges, hero, review, crew, onboarding, settings
NEW_JS = r'''
/* =========================================================== ORDO: profile, goals, challenges */
const BRAND_SVG = '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="15" fill="#0C0D11"/><circle cx="32" cy="32" r="17.5" fill="none" stroke="#F3F1EC" stroke-width="6.6" stroke-linecap="round" stroke-dasharray="74 200" stroke-dashoffset="-27" transform="rotate(-90 32 32)"/><circle cx="32" cy="32" r="17.5" fill="none" stroke="#F3F1EC" stroke-width="6.6" stroke-linecap="round" stroke-dasharray="0 200" transform="rotate(-90 32 32)"/><path d="M38.4 15.7a17.5 17.5 0 0 1 9.6 9.9" fill="none" stroke="#7C8BFF" stroke-width="6.6" stroke-linecap="round"/><path d="M48.8 33.4A17.5 17.5 0 1 1 30.6 14.6" fill="none" stroke="#F3F1EC" stroke-width="6.6" stroke-linecap="round"/></svg>';
const profile = () => settings.profile || {name: "", schedule: true};
const useSchedule = () => profile().schedule !== false;
const goalsList = () => settings.goals || [];
const PROGRAMS = {
  "75hard": {name:"75 Hard", tag:"Strict", sub:"Two 45-minute workouts (one outdoors), a healthy diet, a gallon of water, no alcohol or cheat meals, 10 pages and a progress photo. Every day for 75 days. Miss one and you're back to Day 1.",
    challenge:{name:"75 Hard", length:75, strict:true},
    goals:[
      {id:"w_out", icon:"tree", short:"Outdoor", name:"45-min outdoor workout", type:"time", target:45, unit:"min", step:5, workout:true},
      {id:"w_in", icon:"dumbbell", short:"Indoor", name:"45-min indoor workout", type:"time", target:45, unit:"min", step:5, workout:true},
      {id:"diet", icon:"plate", short:"Diet", name:"Follow a healthy diet plan", type:"check"},
      {id:"water", icon:"glass", short:"Water", name:"Drink a gallon of water", type:"count", target:3.8, unit:"L", step:0.25},
      {id:"alcohol", icon:"nobottle", short:"No alcohol", name:"No alcohol or cheat meals", type:"check"},
      {id:"read", icon:"book", short:"Read", name:"Read 10 pages of self-help", type:"count", target:10, unit:"pages", step:1},
      {id:"photo", icon:"camera", short:"Photo", name:"Take a progress photo", type:"check"},
    ]},
  "75soft": {name:"75 Soft", tag:"Forgiving", sub:"One 45-minute workout, eat well (drink only socially), 3 litres of water and 10 pages, for 75 days. A missed day doesn't reset you.",
    challenge:{name:"75 Soft", length:75, strict:false},
    goals:[
      {id:"w1", icon:"dumbbell", short:"Workout", name:"45-min workout", type:"time", target:45, unit:"min", step:5, workout:true},
      {id:"eat", icon:"plate", short:"Eat well", name:"Eat well. Drink only socially", type:"check"},
      {id:"water", icon:"glass", short:"Water", name:"Drink 3 litres of water", type:"count", target:3, unit:"L", step:0.25},
      {id:"read", icon:"book", short:"Read", name:"Read 10 pages", type:"count", target:10, unit:"pages", step:1},
    ]},
  "builder": {name:"Builder Day", tag:"Timed schedule", sub:"A full-time builder's day in 14 timed blocks: the Daily Five, rep counters, records and a guided full-body workout.", schedule:true, goals:[]},
  "custom": {name:"Your own goals", tag:"Blank", sub:"Start empty and set the daily goals you want to hit.", goals:[]},
};
const goalDone = (g, v) => g.type === "check" ? !!v : (Number(v) || 0) >= (Number(g.target) || 0) && (Number(g.target) || 0) > 0;
const fmtGoal = (g, v) => g.type === "time" ? String(Math.round(v)) : (Math.round(v * 100) / 100).toString();
function goalProgress(k){
  const G = goalsList(), gv = getDay(k).goals || {};
  const done = G.filter(g => goalDone(g, gv[g.id])).length;
  return {done, total: G.length, frac: G.length ? done / G.length : 0};
}
const daysBetween = (a, b) => Math.round((fromKey(b) - fromKey(a)) / 864e5);
/** Where the challenge stands. Strict challenges restart the day after any missed day. */
function challengeState(today){
  const c = settings.challenge; if (!c || !c.start || !goalsList().length) return null;
  let start = c.start, restarts = 0;
  if (c.strict) for (let k = c.start; k < today; k = shift(k, 1)) if (goalProgress(k).frac < 1) { start = shift(k, 1); restarts++; }
  const dayN = daysBetween(start, today) + 1;
  const kept = c.strict ? Math.max(0, dayN - 1) : (() => { let n = 0; for (let k = c.start; k < today; k = shift(k, 1)) if (goalProgress(k).frac >= 1) n++; return n; })();
  return {name: c.name, length: c.length || 75, start, dayN: Math.min(dayN, c.length || 75), restarts, strict: !!c.strict,
    finished: kept >= (c.length || 75), kept, todayDone: goalProgress(today).frac >= 1};
}
function setGoal(id, v){
  const d = ensure(sel); d.goals = {...(d.goals || {})};
  if (v === null || v === false || v === 0) delete d.goals[id]; else d.goals[id] = v;
  saveDay(d, false); render();
}
function applyProgram(key, startToday){
  const P = PROGRAMS[key];
  settings.profile = {...profile(), program: key, schedule: !!P.schedule || (key === "builder")};
  if (key === "builder") settings.profile.schedule = true;
  settings.goals = P.goals.map(g => ({...g}));
  settings.challenge = P.challenge ? {...P.challenge, start: startToday ? keyOf(new Date()) : (settings.challenge || {}).start || keyOf(new Date())} : null;
  saveSettings();
}

/* ---------- hero ---------- */
function ringSVG(frac){
  const r = 52, c = 2 * Math.PI * r, f = Math.max(0, Math.min(1, frac));
  return `<svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="${r}" fill="none" stroke="rgba(243,241,236,.1)" stroke-width="10"/>
    <circle cx="60" cy="60" r="${r}" fill="none" stroke="#7C8BFF" stroke-width="10" stroke-linecap="round" stroke-dasharray="${(c * f).toFixed(1)} ${c.toFixed(1)}"/></svg>`;
}
function renderHero(today){
  const d = fromKey(sel), isToday = sel === today, h = new Date().getHours();
  const name = (profile().name || "").split(" ")[0];
  $("heroDate").textContent = d.toLocaleDateString(undefined, {weekday: "long", day: "numeric", month: "long"});
  $("heroHi").textContent = isToday ? `${h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening"}${name ? ", " + name : ""}.` : d.toLocaleDateString(undefined, {weekday: "long"}) + ".";
  const chips = $("heroChips"); chips.innerHTML = "";
  const chip = (html, cls) => { const e = document.createElement("span"); e.className = "hchip" + (cls ? " " + cls : ""); e.innerHTML = html; chips.appendChild(e); };
  const cs = challengeState(today);
  if (cs) chip(cs.finished ? `<b>${cs.name}</b> complete` : `${cs.name} <b>Day ${cs.dayN}</b> / ${cs.length}`, cs.restarts && cs.dayN === 1 ? "warn" : "accent");
  if (goalsList().length) { const g = goalProgress(sel); chip(`Goals <b>${g.done}/${g.total}</b>`); }
  if (useSchedule()) chip(`The Five <b>${fiveCount(getDay(sel))}/5</b>`);
  const L = acct().start ? stakeLedger(today) : null;
  if (L && L.owed) chip(`Owed <b>${naira(L.owed)}</b>`, "warn");
  const sc = scoreDay(sel);
  $("heroRing").innerHTML = ringSVG(sc ? sc.score / 100 : 0) + `<div class="rv"><b>${sc ? sc.grade : "—"}</b><span>${sc ? sc.score + " / 100" : "No score"}</span></div>`;
}

/* ---------- goals panel ---------- */
let editingGoals = false, goalDraft = [];
function renderGoals(today){
  const box = $("goals"); box.innerHTML = "";
  const G = goalsList(), cs = challengeState(today), day = getDay(sel), gv = day.goals || {};
  $("goalsTitle").textContent = cs ? cs.name : "Today's goals";
  if (editingGoals) return renderGoalEditor(box);
  if (!G.length) {
    $("goalsMeta").textContent = "";
    const p = document.createElement("div"); p.className = "gedit";
    p.innerHTML = `<p class="beat">Track the goals that matter to you every day, or take on a challenge with your crew.</p><div class="progs"></div>`;
    ["75hard", "75soft", "custom"].forEach(k => {
      const P = PROGRAMS[k], c = document.createElement("button"); c.className = "prog-card";
      c.innerHTML = `<b></b><span></span><i></i>`; c.querySelector("b").textContent = P.name; c.querySelector("span").textContent = P.sub; c.querySelector("i").textContent = P.tag;
      c.onclick = () => { if (k === "custom") { goalDraft = [newGoal()]; editingGoals = true; settings.profile = {...profile(), program: "custom"}; } else applyProgram(k, true); render(); };
      p.querySelector(".progs").appendChild(c);
    });
    box.appendChild(p);
    return;
  }
  const prog = goalProgress(sel);
  $("goalsMeta").textContent = `${prog.done} / ${prog.total} done`;
  if (cs) {
    const ch = document.createElement("div"); ch.className = "chal";
    const status = cs.finished ? "Complete. Every day kept." : cs.todayDone ? "Today's kept. Come back tomorrow." : cs.strict ? "Finish every goal today or it's back to Day 1." : "Finish every goal to keep the streak.";
    ch.innerHTML = `<div class="dn">${cs.dayN}<small> / ${cs.length}</small></div><div><div class="nm"></div><div class="st"></div></div><div class="st" style="text-align:right">${cs.restarts ? `${cs.restarts} restart${cs.restarts > 1 ? "s" : ""}` : "No restarts"}</div><div class="track"></div>`;
    ch.querySelector(".nm").textContent = `${cs.name} · Day ${cs.dayN}`;
    ch.querySelector(".st").textContent = status;
    const tr = ch.querySelector(".track");
    for (let i = 0; i < cs.length; i++) {
      const k = shift(cs.start, i), cell = document.createElement("i");
      if (k < today && goalProgress(k).frac >= 1) cell.className = "ok";
      else if (k === today) cell.className = cs.todayDone ? "ok" : "today";
      tr.appendChild(cell);
    }
    tr.style.gridTemplateColumns = `repeat(${cs.length},minmax(0,1fr))`;
    box.appendChild(ch);
  }
  G.forEach((g, i) => {
    const v = gv[g.id], done = goalDone(g, v);
    const row = document.createElement("div"); row.className = "goal" + (done ? " done" : "");
    if (g.type === "check") {
      row.innerHTML = `<input type="checkbox" class="chk" id="goal-${i}"><label class="gname" for="goal-${i}"></label><span></span>`;
      row.querySelector("input").checked = done;
      row.querySelector("input").onchange = e => setGoal(g.id, e.target.checked ? true : null);
    } else {
      const step = Number(g.step) || (g.type === "time" ? 5 : 1), n = Number(v) || 0, t = Number(g.target) || 0;
      row.innerHTML = `<input type="checkbox" class="chk" id="goal-${i}" tabindex="-1"><label class="gname" for="goal-${i}"></label>
        <div class="gctl"><button aria-label="Less">−</button><span class="gval"></span><button aria-label="More">+</button></div>
        <div class="gbar"><i style="width:${t ? Math.min(100, Math.round(n / t * 100)) : 0}%"></i></div>`;
      row.querySelector("input").checked = done;
      row.querySelector("input").onchange = e => setGoal(g.id, e.target.checked ? t : null);
      row.querySelector(".gval").textContent = `${fmtGoal(g, n)}/${fmtGoal(g, t)} ${g.unit || ""}`.trim();
      const [minus, plus] = row.querySelectorAll(".gctl button");
      minus.onclick = () => setGoal(g.id, Math.max(0, Math.round((n - step) * 100) / 100) || null);
      plus.onclick = () => setGoal(g.id, Math.round((n + step) * 100) / 100);
      if (g.workout && sel === today) {
        const w = document.createElement("button"); w.className = "linkbtn gwork"; w.textContent = "▶ Guided workout · logs the minutes here";
        w.onclick = () => { pendingGoalId = g.id; startWorkout(repDefs("train", today)); };
        row.appendChild(w);
      }
    }
    row.querySelector(".gname").textContent = g.name;
    box.appendChild(row);
  });
  const foot = document.createElement("div"); foot.className = "redfoot"; foot.style.paddingTop = "12px";
  const ed = document.createElement("button"); ed.className = "linkbtn"; ed.textContent = "Edit goals";
  ed.onclick = () => { goalDraft = goalsList().map(g => ({...g})); editingGoals = true; render(); };
  foot.appendChild(ed);
  box.appendChild(foot);
}
const newGoal = () => ({id: "g" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), name: "", type: "check", target: 1, unit: ""});
function renderGoalEditor(box){
  $("goalsMeta").textContent = "editing";
  const w = document.createElement("div"); w.className = "gedit";
  w.innerHTML = `<div class="redhead" style="grid-template-columns:minmax(0,1fr) 108px 72px 64px 34px"><span>Goal</span><span>Type</span><span>Target</span><span>Unit</span><span></span></div>`;
  goalDraft.forEach((g, i) => {
    const r = document.createElement("div"); r.className = "gedrow";
    r.innerHTML = `<input class="ed gn" maxlength="60" placeholder="e.g. Read 10 pages"><select class="ed gt"><option value="check">Done / not</option><option value="count">Count</option><option value="time">Minutes</option></select>
      <input class="ed gtar" type="number" min="0" step="any" inputmode="decimal"><input class="ed gu" maxlength="10" placeholder="unit"><button class="x" aria-label="Remove">✕</button>`;
    const [nm, , tg, un] = r.querySelectorAll("input"), ty = r.querySelector("select");
    nm.value = g.name; ty.value = g.type; tg.value = g.type === "check" ? "" : g.target; un.value = g.unit || (g.type === "time" ? "min" : "");
    tg.disabled = un.disabled = g.type === "check";
    nm.oninput = () => { g.name = nm.value; };
    ty.onchange = () => { g.type = ty.value; if (g.type === "time") { g.unit = "min"; g.step = 5; g.target = g.target > 1 ? g.target : 30; } render(); };
    tg.oninput = () => { g.target = Number(tg.value) || 0; };
    un.oninput = () => { g.unit = un.value; };
    r.querySelector(".x").onclick = () => { goalDraft.splice(i, 1); render(); };
    w.appendChild(r);
  });
  const f = document.createElement("div"); f.className = "redfoot";
  f.innerHTML = `<button class="btn-sm">Save goals</button><button class="linkbtn">+ Add goal</button><button class="linkbtn">Cancel</button>`;
  const [save, add, cancel] = f.querySelectorAll("button");
  save.onclick = () => { settings.goals = goalDraft.filter(g => g.name.trim()).map(g => ({...g, name: g.name.trim()})); editingGoals = false; saveSettings(); render(); };
  add.onclick = () => { goalDraft.push(newGoal()); render(); };
  cancel.onclick = () => { editingGoals = false; render(); };
  w.appendChild(f);
  const hint = document.createElement("p"); hint.className = "beat";
  hint.textContent = "Change your challenge, or start one, in Settings (the sliders at the top).";
  w.appendChild(hint);
  box.appendChild(w);
}

/* ---------- evening review panel (when the timed schedule is off) ---------- */
function reviewBlock(day){
  const rv = document.createElement("div"); rv.className = "extra"; rv.style.marginTop = "0";
  rv.innerHTML = `<label class="fl">Tomorrow's top 3</label><div class="top3in">${[0,1,2].map(i=>`<span>${i+1}</span><input class="tx" id="top-${i}" maxlength="140" placeholder="Priority ${i+1}">`).join("")}</div>
    <label class="fl" for="grat">One line of gratitude</label><input class="tx" id="grat" maxlength="200" placeholder="Today I'm grateful for…">`;
  [0,1,2].forEach(i => { const inp = rv.querySelector("#top-"+i); inp.value = (day.top3 || [])[i] || ""; inp.oninput = () => { const dd = ensure(sel); dd.top3 = [...(dd.top3 || ["","",""])]; dd.top3[i] = inp.value; saveDay(dd,true); }; });
  const g = rv.querySelector("#grat"); g.value = day.gratitude || ""; g.oninput = () => { const dd = ensure(sel); dd.gratitude = g.value; saveDay(dd,true); };
  rv.appendChild(reflectionBlock(day));
  rv.appendChild(reportButton(sel));
  return rv;
}

/* ---------- layout by program ---------- */
let lastNativeSchedule = null;
function applyLayout(){
  const sch = useSchedule();
  document.querySelectorAll(".p-sched,.p-five,.p-heat").forEach(e => e.hidden = !sch);
  $("reviewPanel").hidden = sch;
  $("goalsPanel").hidden = sch && !goalsList().length && profile().program === undefined && !!settings.profile === false ? false : false;
  if (NATIVE && NATIVE.setScheduleEnabled && lastNativeSchedule !== sch) { try { NATIVE.setScheduleEnabled(sch); lastNativeSchedule = sch; } catch(e){} }
}

/* =========================================================== crew */
const crewState = {members: [], code: null, unsub: null, last: ""};
const crewFS = () => window.__ordo && window.__ordo.db && window.__ordo.uid ? window.__ordo : null;
function crewSummary(today){
  const cs = challengeState(today), sc = scoreDay(today), g = goalProgress(today), me = crewFS();
  return {name: (profile().name || (me && me.user.displayName) || "Member").slice(0, 40), photo: (me && me.user.photoURL) || "",
    challenge: cs ? {name: cs.name, day: cs.dayN, length: cs.length, restarts: cs.restarts, done: cs.todayDone} : null,
    today: {date: today, done: g.done, total: g.total, five: useSchedule() ? fiveCount(getDay(today)) : null},
    grade: sc ? sc.grade : null, score: sc ? sc.score : null};
}
let crewPushTimer = null;
function pushCrew(){
  const fs = crewFS(), crews = settings.crews || [];
  if (!fs || !crews.length) return;
  clearTimeout(crewPushTimer);
  crewPushTimer = setTimeout(() => {
    const sum = crewSummary(keyOf(new Date())), sig = JSON.stringify(sum);
    if (sig === crewState.last) return;
    crewState.last = sig;
    crews.forEach(code => fs.db.collection("groups").doc(code).collection("members").doc(fs.uid)
      .set({...sum, updated: firebase.firestore.FieldValue.serverTimestamp()}, {merge: true}).catch(() => {}));
  }, 1500);
}
function watchCrew(){
  const fs = crewFS(), code = (settings.crews || [])[0] || null;
  if (crewState.code === code && crewState.unsub) return;
  if (crewState.unsub) { crewState.unsub(); crewState.unsub = null; }
  crewState.code = code; crewState.members = [];
  if (!fs || !code) return;
  fs.db.collection("groups").doc(code).get().then(doc => { crewState.name = doc.exists ? doc.data().name : code; renderCrew(); }).catch(() => {});
  crewState.unsub = fs.db.collection("groups").doc(code).collection("members").onSnapshot(snap => {
    crewState.members = snap.docs.map(d => ({uid: d.id, ...d.data()}));
    renderCrew();
  }, () => {});
}
const crewCode = () => Array.from(crypto.getRandomValues(new Uint8Array(6))).map(n => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[n % 32]).join("");
async function createCrew(name){
  const fs = crewFS(); if (!fs) return;
  const code = crewCode();
  await fs.db.collection("groups").doc(code).set({name: name || "Our crew", owner: fs.uid, created: firebase.firestore.FieldValue.serverTimestamp()});
  settings.crews = [code, ...(settings.crews || [])]; saveSettings(); crewState.last = ""; pushCrew(); watchCrew(); renderCrew();
}
async function joinCrew(code){
  const fs = crewFS(); if (!fs) return "Sign in first.";
  code = code.toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (code.length !== 6) return "Crew codes are 6 characters.";
  const doc = await fs.db.collection("groups").doc(code).get().catch(() => null);
  if (!doc || !doc.exists) return "No crew with that code. Check it with whoever invited you.";
  settings.crews = [code, ...(settings.crews || []).filter(c => c !== code)]; saveSettings();
  crewState.last = ""; pushCrew(); watchCrew(); renderCrew();
  return "";
}
function renderCrew(){
  const panel = $("crewPanel"), box = $("crew");
  const fs = crewFS();
  panel.hidden = !fs;
  if (!fs) return;
  box.innerHTML = "";
  const code = (settings.crews || [])[0];
  if (!code) {
    $("crewMeta").textContent = "";
    box.innerHTML = `<p class="beat">Do your challenge with friends. Everyone in a crew sees each other's day count and today's progress, nothing else.</p>
      <label class="fl" for="crewName">Start a crew</label><div class="crewjoin"><input class="tx ed" id="crewName" maxlength="40" placeholder="Crew name, e.g. 75 Hard Lagos"><button class="btn accent" id="crewCreate">Create</button></div>
      <label class="fl" for="crewCodeIn">Or join one</label><div class="crewjoin"><input class="tx ed" id="crewCodeIn" maxlength="8" placeholder="6-character code" style="text-transform:uppercase;letter-spacing:.2em"><button class="btn" id="crewJoin">Join</button></div>
      <p class="beat" id="crewMsg"></p>`;
    box.querySelector("#crewCreate").onclick = () => createCrew(box.querySelector("#crewName").value.trim()).catch(e => box.querySelector("#crewMsg").textContent = "Couldn't create the crew: " + e.message);
    box.querySelector("#crewJoin").onclick = async () => { box.querySelector("#crewMsg").textContent = (await joinCrew(box.querySelector("#crewCodeIn").value)) || ""; };
    return;
  }
  const today = keyOf(new Date());
  $("crewMeta").textContent = `${crewState.members.length} member${crewState.members.length === 1 ? "" : "s"}`;
  const head = document.createElement("div"); head.className = "crewhead";
  head.innerHTML = `<b></b><code title="Tap to copy the invite code"></code>`;
  head.querySelector("b").textContent = crewState.name || "Crew";
  head.querySelector("code").textContent = code;
  head.querySelector("code").onclick = () => navigator.clipboard && navigator.clipboard.writeText(code).catch(() => {});
  box.appendChild(head);
  const ms = [...crewState.members].sort((a, b) => {
    const ad = a.challenge ? a.challenge.day : 0, bd = b.challenge ? b.challenge.day : 0;
    if (bd !== ad) return bd - ad;
    const af = a.today && a.today.date === today && a.today.total ? a.today.done / a.today.total : 0;
    const bf = b.today && b.today.date === today && b.today.total ? b.today.done / b.today.total : 0;
    return bf - af;
  });
  if (!ms.length) { const p = document.createElement("p"); p.className = "beat"; p.textContent = "Loading the crew…"; box.appendChild(p); }
  ms.forEach((m, i) => {
    const row = document.createElement("div"); row.className = "member" + (m.uid === fs.uid ? " me" : "");
    const fresh = m.today && m.today.date === today;
    const frac = fresh && m.today.total ? m.today.done / m.today.total : 0;
    row.innerHTML = `<span class="pos">${i + 1}</span><span class="pic"></span><div style="min-width:0"><div class="mn"></div><div class="ms"></div></div>
      <div class="md"><b></b><span></span></div><div class="mbar"><i style="width:${Math.round(frac * 100)}%"></i></div>`;
    const pic = row.querySelector(".pic");
    if (m.photo) { const im = document.createElement("img"); im.src = m.photo; im.alt = ""; im.referrerPolicy = "no-referrer"; pic.appendChild(im); }
    else pic.textContent = (m.name || "?").trim().charAt(0).toUpperCase();
    row.querySelector(".mn").textContent = (m.name || "Member") + (m.uid === fs.uid ? " (you)" : "");
    row.querySelector(".ms").textContent = fresh ? `Today ${m.today.done}/${m.today.total}${m.grade ? " · " + m.grade : ""}` : "Not updated today";
    row.querySelector(".md b").textContent = m.challenge ? m.challenge.day : "—";
    row.querySelector(".md span").textContent = m.challenge ? `day / ${m.challenge.length}` : "no challenge";
    box.appendChild(row);
  });
  const f = document.createElement("div"); f.className = "redfoot";
  const inv = document.createElement("a"); inv.className = "linkbtn"; inv.target = "_blank"; inv.rel = "noopener";
  inv.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(`Join my crew on ORDO for ${(settings.challenge || {}).name || "our challenge"}.\n\n1. Open ${location.origin}${location.pathname}\n2. Sign in with Google\n3. Crew → Join → code ${code}`)}`;
  inv.textContent = "Invite on WhatsApp";
  const leave = document.createElement("button"); leave.className = "linkbtn"; leave.style.color = "var(--muted)"; leave.textContent = "Leave crew";
  leave.onclick = () => { fs.db.collection("groups").doc(code).collection("members").doc(fs.uid).delete().catch(() => {}); settings.crews = (settings.crews || []).filter(c => c !== code); saveSettings(); watchCrew(); renderCrew(); };
  f.append(inv, leave);
  box.appendChild(f);
}

/* =========================================================== onboarding + settings */
function onboarding(step, ctx = {}){
  const o = openOverlay(), today = keyOf(new Date());
  o.innerHTML = `<div class="ob"><div class="mark">${BRAND_SVG}<span>ORDO</span></div><div class="obbody" style="display:grid;gap:18px"></div></div>`;
  const b = o.querySelector(".obbody");
  if (step === "welcome") {
    b.innerHTML = `<h2>Discipline, kept.</h2><p class="lead">Daily goals, challenges like 75 Hard, guided workouts, an honest grade every day, and a crew that sees whether you showed up.</p>
      <div style="display:grid;gap:10px"><button class="btn primary block" id="obSign"><span>Sign in with Google</span></button><button class="btn block" id="obLocal">Continue without an account</button></div>
      <p class="beat">Signing in keeps your progress on every device and lets you join a crew.</p>`;
    b.querySelector("#obSign").onclick = () => { window.__ordoSignIn && window.__ordoSignIn(); };
    b.querySelector("#obLocal").onclick = () => onboarding("name");
  } else if (step === "name") {
    const me = crewFS();
    b.innerHTML = `<h2>What should we call you?</h2><input class="tx" id="obName" maxlength="40" placeholder="First name" style="font-size:20px;padding:14px 16px"><button class="btn primary block" id="obNext">Continue</button>`;
    b.querySelector("#obName").value = profile().name || (me && me.user.displayName ? me.user.displayName.split(" ")[0] : "");
    b.querySelector("#obNext").onclick = () => { settings.profile = {...profile(), name: b.querySelector("#obName").value.trim()}; saveSettings(); onboarding("program"); };
  } else if (step === "program") {
    b.innerHTML = `<h2>Pick your program.</h2><p class="lead">You can change it any time in Settings.</p><div class="progs"></div>`;
    ["75hard", "75soft", "builder", "custom"].forEach(k => {
      const P = PROGRAMS[k], c = document.createElement("button"); c.className = "prog-card";
      c.innerHTML = `<b></b><span></span><i></i>`; c.querySelector("b").textContent = P.name; c.querySelector("span").textContent = P.sub; c.querySelector("i").textContent = P.tag;
      c.onclick = () => {
        if (k === "builder") { settings.profile = {...profile(), program: "builder", schedule: true}; settings.goals = []; settings.challenge = null; saveSettings(); onboarding("crew"); }
        else if (k === "custom") { settings.profile = {...profile(), program: "custom", schedule: false}; settings.goals = []; settings.challenge = null; saveSettings(); onboarding("crew"); }
        else { settings.profile = {...profile(), schedule: false}; applyProgram(k, true); onboarding("crew"); }
      };
      b.querySelector(".progs").appendChild(c);
    });
  } else if (step === "crew") {
    const fs = crewFS();
    b.innerHTML = `<h2>Bring your crew.</h2><p class="lead">${fs ? "Join a friend's crew with their code, or start one from the Crew panel and invite them." : "Sign in to do this with friends. You can do it later from the Crew panel."}</p>
      ${fs ? `<div class="crewjoin"><input class="tx" id="obCode" maxlength="8" placeholder="Crew code" style="text-transform:uppercase;letter-spacing:.2em"><button class="btn" id="obJoin">Join</button></div><p class="beat" id="obMsg"></p>` : ""}
      <button class="btn primary block" id="obDone">${fs ? "Skip for now" : "Start"}</button>`;
    if (fs) b.querySelector("#obJoin").onclick = async () => {
      const msg = await joinCrew(b.querySelector("#obCode").value);
      if (msg) b.querySelector("#obMsg").textContent = msg; else { closeOverlay(); render(); }
    };
    b.querySelector("#obDone").onclick = () => { closeOverlay(); render(); };
  }
}
function openSettings(){
  const o = openOverlay(), fs = crewFS(), p = profile(), c = settings.challenge;
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">Settings</span><button class="close">✕ Close</button></div>
    <h2 class="exname">Settings</h2>
    <div class="setgrp"><h3>You</h3><label class="fl" for="stName">Name</label><input class="tx" id="stName" maxlength="40">
      <div class="beat" id="stWho"></div></div>
    <div class="setgrp"><h3>Program</h3><div class="progs" id="stProgs"></div>
      <label class="toggle"><span>Timed daily schedule (Builder Day blocks, the Five, alarms)</span><input type="checkbox" id="stSched"></label></div>
    <div class="setgrp"><h3>Challenge</h3><div id="stChal"></div></div>
    <div class="setgrp"><h3>Appearance</h3><div class="seg" id="stTheme"><button data-t="system">System</button><button data-t="dark">Dark</button><button data-t="light">Light</button></div></div>
    <div class="setgrp"><h3>Account</h3><div id="stAcct"></div></div></div>`;
  o.querySelector(".close").onclick = () => { closeOverlay(); render(); };
  const nm = o.querySelector("#stName"); nm.value = p.name || "";
  nm.onchange = () => { settings.profile = {...profile(), name: nm.value.trim()}; saveSettings(); };
  o.querySelector("#stWho").textContent = fs ? `Signed in as ${fs.user.email || fs.user.displayName}` : "Not signed in. Your data stays on this device.";
  const progs = o.querySelector("#stProgs");
  ["75hard", "75soft", "custom"].forEach(k => {
    const P = PROGRAMS[k], card = document.createElement("button"); card.className = "prog-card" + (p.program === k ? " on" : "");
    card.innerHTML = `<b></b><span></span><i></i>`; card.querySelector("b").textContent = P.name; card.querySelector("span").textContent = P.sub; card.querySelector("i").textContent = p.program === k ? "Current" : "Switch";
    card.onclick = () => {
      if (p.program === k) return;
      card.querySelector("i").textContent = "Tap again to confirm"; card.classList.add("on");
      card.onclick = () => { if (k === "custom") { settings.profile = {...profile(), program: "custom"}; settings.goals = []; settings.challenge = null; saveSettings(); } else applyProgram(k, true); openSettings(); };
    };
    progs.appendChild(card);
  });
  const sch = o.querySelector("#stSched"); sch.checked = useSchedule();
  sch.onchange = () => { settings.profile = {...profile(), schedule: sch.checked}; saveSettings(); };
  const chal = o.querySelector("#stChal");
  if (c && c.start) {
    const cs = challengeState(keyOf(new Date()));
    chal.innerHTML = `<p class="beat"><b></b></p><label class="fl" for="stStart">Day 1 was</label><input class="tx" type="date" id="stStart">
      <label class="toggle"><span>Strict: a missed goal restarts you at Day 1</span><input type="checkbox" id="stStrict"></label>
      <div class="redfoot"><button class="linkbtn" id="stRestart">Restart from today</button><button class="linkbtn" id="stStop" style="color:var(--warn)">End the challenge</button></div>`;
    chal.querySelector("b").textContent = cs ? `${cs.name}: Day ${cs.dayN} of ${cs.length}${cs.restarts ? ` · ${cs.restarts} restart${cs.restarts > 1 ? "s" : ""}` : ""}` : c.name;
    const st = chal.querySelector("#stStart"); st.value = c.start; st.onchange = () => { settings.challenge = {...c, start: st.value}; saveSettings(); openSettings(); };
    const sx = chal.querySelector("#stStrict"); sx.checked = !!c.strict; sx.onchange = () => { settings.challenge = {...settings.challenge, strict: sx.checked}; saveSettings(); };
    chal.querySelector("#stRestart").onclick = () => { settings.challenge = {...settings.challenge, start: keyOf(new Date())}; saveSettings(); openSettings(); };
    chal.querySelector("#stStop").onclick = () => { settings.challenge = null; saveSettings(); openSettings(); };
  } else {
    chal.innerHTML = `<p class="beat">No challenge running. Your goals still count toward your daily grade.</p><div class="redfoot"><button class="btn-sm" id="stStartC">Start a 75-day challenge with my goals</button></div>`;
    chal.querySelector("#stStartC").onclick = () => { settings.challenge = {name: "75 Days", length: 75, strict: true, start: keyOf(new Date())}; saveSettings(); openSettings(); };
    if (!goalsList().length) chal.querySelector("#stStartC").disabled = true;
  }
  const th = (() => { try { return localStorage.getItem("ordo-theme") || "system"; } catch(e) { return "system"; } })();
  o.querySelectorAll("#stTheme button").forEach(btn => {
    btn.classList.toggle("on", btn.dataset.t === th);
    btn.onclick = () => {
      try { localStorage.setItem("ordo-theme", btn.dataset.t); } catch(e){}
      if (btn.dataset.t === "system") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", btn.dataset.t);
      o.querySelectorAll("#stTheme button").forEach(x => x.classList.toggle("on", x === btn));
    };
  });
  const ac = o.querySelector("#stAcct");
  if (fs) { const out = document.createElement("button"); out.className = "btn"; out.textContent = "Sign out"; out.onclick = () => { window.__ordoSignOut && window.__ordoSignOut(); closeOverlay(); }; ac.appendChild(out); }
  else if (window.__ordoSignIn) { const inb = document.createElement("button"); inb.className = "btn primary"; inb.textContent = "Sign in with Google"; inb.onclick = () => { closeOverlay(); window.__ordoSignIn(); }; ac.appendChild(inb); }
}
'''
rep('''/* ---------- boot ---------- */
lsLoad();
render();''', NEW_JS + '''
/* ---------- boot ---------- */
$("brandMark").innerHTML = BRAND_SVG;
$("settingsBtn").onclick = openSettings;
lsLoad();
render();''')

# =============================================================== render(): hero, goals, layout, crew, review
rep('''function render(){
  const today = keyOf(new Date());
  const day = getDay(sel);
  const d = fromKey(sel);''', '''function render(){
  const today = keyOf(new Date());
  const day = getDay(sel);
  const d = fromKey(sel);
  applyLayout();
  renderHero(today);
  renderGoals(today);
  if (!useSchedule()) { const rv = $("review"); if (!editing() || !rv.contains(document.activeElement)) { rv.innerHTML = ""; rv.appendChild(reviewBlock(day)); } }
  pushCrew(); renderCrew();''')
rep('''  $("dlabel").textContent = sel === today ? "Today · " + d.toLocaleDateString(undefined,{weekday:"short",day:"numeric",month:"short"})
                                           : d.toLocaleDateString(undefined,{weekday:"short",day:"numeric",month:"short",year:"numeric"});''',
    '''  $("dlabel").textContent = sel === today ? "Today" : d.toLocaleDateString(undefined,{weekday:"short",day:"numeric",month:"short"});''')
# the schedule's own pieces only when it's on
rep('''  // now bar
  const nb = $("nowbar"); let curId = "";
  if (sel === today) {''', '''  // now bar
  const nb = $("nowbar"); let curId = "";
  if (sel === today && useSchedule()) {''')
rep('''      rv.innerHTML = `<label class="fl">Tomorrow's top 3</label>''', '''      rv.remove(); ex.appendChild(reviewBlock(day));
      if (false) rv.innerHTML = `<label class="fl">Tomorrow's top 3</label>''')
rep('''    p.textContent = "Nothing set last night. Write tomorrow's top 3 in tonight's REVIEW block and it shows here in the morning.";''',
    '''    p.textContent = useSchedule() ? "Nothing set last night. Write tomorrow's top 3 in tonight's REVIEW block and it shows here in the morning." : "Nothing set last night. Write tomorrow's top 3 in tonight's Evening review and it shows here in the morning.";''')

# =============================================================== boot: expose Firebase to crew + onboarding
rep('''  let unsub = null;
  const authBox = $("auth");''', '''  let unsub = null;
  const authBox = $("auth");
  const signIn = () => {
    if (NATIVE) { $("storeNote").textContent = "Choose your Google account…"; NATIVE.signInWithGoogle(); return; }
    const p = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(p).catch(e => {
      if (["auth/popup-blocked","auth/operation-not-supported-in-this-environment","auth/cancelled-popup-request"].includes(e.code)) auth.signInWithRedirect(p);
      else if (e.code !== "auth/popup-closed-by-user") $("storeNote").textContent = "Sign-in didn't work: " + (e.message || e.code);
    });
  };
  window.__ordoSignIn = signIn;
  window.__ordoSignOut = () => { auth.signOut(); if (NATIVE) NATIVE.signOut(); };''')
rep('''    if (!u) {
      LS_KEY = "builder-day-v2"; lsLoad(); render();''', '''    window.__ordo = u ? {db, uid: u.uid, user: u} : null;
    if (crewState.unsub) { crewState.unsub(); crewState.unsub = null; crewState.code = null; }
    if (!u) {
      LS_KEY = "builder-day-v2"; lsLoad(); render();
      if (!Object.keys(days).length && !settings.profile && !sessionStorage.getItem("ordo-local")) onboarding("welcome");''')
rep('''    unsub = store.subscribe(snap => {
      $("storeNote").textContent = "Synced to your account. Private to you, on every device you sign in on.";''', '''    if (!ovl().hidden && ovl().querySelector(".ob")) closeOverlay();
    unsub = store.subscribe(snap => {
      $("storeNote").textContent = "Synced to your account.";
      // a brand-new account goes through setup; an existing one (with days already logged) keeps its schedule
      if (!settings.profile) {
        if (Object.keys(days).length || (local && local.days && Object.keys(local.days).length)) { settings.profile = {name: (u.displayName || "").split(" ")[0], schedule: true, program: "builder"}; saveSettings(); }
        else setTimeout(() => onboarding("name"), 50);
      }
      watchCrew(); renderCrew();''')
rep('''    const who = document.createElement("span"); who.className = "who"; who.textContent = u.email || u.displayName || "Signed in";
    const out = document.createElement("button"); out.className = "dir"; out.textContent = "Sign out";
    out.onclick = () => { auth.signOut(); if (NATIVE) NATIVE.signOut(); };
    authBox.append(who, out);''', '''    // account details live in Settings now''')
rep('''      const b = document.createElement("button"); b.className = "btn-g"; b.innerHTML = G_ICON + "<span>Sign in with Google</span>";
      b.onclick = () => {
        if (NATIVE) { $("storeNote").textContent = "Choose your Google account…"; NATIVE.signInWithGoogle(); return; }
        const p = new firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(p).catch(e => {
          if (["auth/popup-blocked","auth/operation-not-supported-in-this-environment","auth/cancelled-popup-request"].includes(e.code)) auth.signInWithRedirect(p);
          else if (e.code !== "auth/popup-closed-by-user") $("storeNote").textContent = "Sign-in didn't work: " + (e.message || e.code);
        });
      };
      authBox.appendChild(b);''', '''      const b = document.createElement("button"); b.className = "btn-g"; b.innerHTML = G_ICON + "<span>Sign in with Google</span>";
      b.onclick = signIn;
      authBox.appendChild(b);''')
rep('''    b.querySelector("#obLocal").onclick = () => onboarding("name");''', '''    b.querySelector("#obLocal").onclick = () => { try { sessionStorage.setItem("ordo-local", "1"); } catch(e){} onboarding("name"); };''')

open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ORDO patch applied:", len(s), "chars")
