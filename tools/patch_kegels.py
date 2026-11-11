"""One-off: an optional "Pelvic floor" area (kegels) people can add from the workout builder. Not in the default workout.
Kegels have nothing to watch, so their guide shows a pacing ring (closes = squeeze, opens = relax) instead of a video."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()

def rep(a, b):
    global s
    assert s.count(a) == 1, f"{s.count(a)} matches: " + a[:90]
    s = s.replace(a, b)

# exercise guides (no video: a pacing ring instead)
rep('''// Your FULL BODY TRAIN 10 routine''', r'''// Pelvic floor (kegels): optional, added from the workout builder. rhythm = [squeeze s, relax s] for the pacing ring.
Object.assign(EXERCISES, {
  kegelfind: {name:"Find the muscle", rhythm:[3, 3], muscles:["Pelvic floor"],
    steps:["Sit or lie down, relaxed. Breathe normally.","Squeeze as if stopping the flow of urine and holding in gas at the same time. You should feel a lift inside, behind the base of the penis / up toward the navel.","Keep your glutes, thighs and stomach loose. Only the inside lifts.","Let go fully. That lift-and-release is one kegel. Never practise while actually urinating."],
    mistakes:["Squeezing glutes, thighs or abs instead","Holding your breath","Bearing down (pushing out) instead of lifting"]},
  kegelhold: {name:"Kegel Holds", rhythm:[10, 10], muscles:["Pelvic floor","Endurance"],
    steps:["Lie on your back, knees bent, or sit tall.","Lift and squeeze the pelvic floor, then hold for 10 seconds while breathing normally.","Release completely and rest 10 seconds. The rest matters as much as the squeeze.","Build up: start with 5-second holds if 10 is too much; add a second each week."],
    mistakes:["Holding your breath through the squeeze","Not relaxing fully between reps","Letting the squeeze fade halfway: stop the rep when it fades"]},
  kegelflick: {name:"Quick Flicks", rhythm:[1, 1], muscles:["Pelvic floor","Fast-twitch"],
    steps:["Same position as the holds.","Squeeze hard and fast, then let go straight away: about one second each.","Keep them crisp, like a pulse. Breathe throughout.","These train the fast reflex that fires during sudden effort and control."],
    mistakes:["Getting sloppy as you tire: stop when they lose snap","Tensing the abs or glutes"]},
  kegelelev: {name:"Elevator Kegels", rhythm:[9, 6], muscles:["Pelvic floor","Control"],
    steps:["Picture the pelvic floor as a lift going up three floors.","Squeeze a third of the way and pause 3 s, two thirds and pause 3 s, then all the way and pause 3 s.","Come down the same way, one floor at a time, then relax fully.","Slow and controlled: this builds precise, graded control."],
    mistakes:["Rushing the floors","Losing the squeeze on the way down"]},
  kegelbridge: {name:"Bridge + Kegel", rhythm:[5, 4], muscles:["Pelvic floor","Glutes","Core"],
    steps:["Lie on your back, knees bent, feet flat, hip-width apart.","Breathe out, lift and squeeze the pelvic floor, then drive your hips up into a bridge.","Hold the top 5 seconds keeping both squeezes on.","Lower slowly, then release the pelvic floor fully before the next rep."],
    mistakes:["Arching the lower back at the top","Forgetting the pelvic floor once the hips rise"]},
  kegelstand: {name:"Standing Kegel Holds", rhythm:[10, 10], muscles:["Pelvic floor","Function"],
    steps:["Stand tall, feet hip-width, knees soft.","Lift and squeeze for 10 seconds, breathing normally. Standing is harder: gravity is pulling down.","Release completely for 10 seconds.","Once easy, practise the squeeze just before a cough, a lift, or getting up from a chair (“the knack”)."],
    mistakes:["Clenching the glutes to help","Locking the knees"]},
  kegelrev: {name:"Reverse Kegels (relax & drop)", rhythm:[5, 5], muscles:["Pelvic floor","Relaxation"],
    steps:["Lie or sit relaxed. Breathe deep into your belly.","As you breathe in, let the pelvic floor soften and gently drop, as if letting go of a held breath down there. No pushing or straining.","Breathe out and let it return to rest.","These keep the muscle from getting tight and overworked. Do them after every kegel session."],
    mistakes:["Straining or bearing down hard","Skipping them: a tight pelvic floor works worse, not better"]},
});
const EXTRA_LIB = [   // not in the default workout; offered as their own area in the builder
  {id:"kegel_find",  ex:"kegelfind",  sec:"Pelvic floor", name:"Find the muscle (first sessions)", target:5},
  {id:"kegel_hold",  ex:"kegelhold",  sec:"Pelvic floor", name:"Kegel Holds · 10 s", target:10, hint:"10 s squeeze · 10 s rest"},
  {id:"kegel_flick", ex:"kegelflick", sec:"Pelvic floor", name:"Quick Flicks", target:20},
  {id:"kegel_elev",  ex:"kegelelev",  sec:"Pelvic floor", name:"Elevator Kegels", target:5},
  {id:"kegel_bridge",ex:"kegelbridge",sec:"Pelvic floor", name:"Bridge + Kegel · 5 s hold", target:10},
  {id:"kegel_stand", ex:"kegelstand", sec:"Pelvic floor", name:"Standing Kegel Holds · 10 s", target:5},
  {id:"kegel_rev",   ex:"kegelrev",   sec:"Pelvic floor", name:"Reverse Kegels (relax)", target:10, stretch:true},
];

// Your FULL BODY TRAIN 10 routine''')

# no video → pacing ring
rep('''function videoBox(e, autoplay){
  const box = document.createElement("div"); box.className = "vid";''', '''function videoBox(e, autoplay){
  const box = document.createElement("div"); box.className = "vid";
  if (!e.video) {
    const [sq, rl] = e.rhythm || [5, 5], T = sq + rl;
    box.classList.add("pace");
    box.style.setProperty("--T", T + "s"); box.style.setProperty("--sq", (sq / T * 100).toFixed(1) + "%");
    box.innerHTML = `<div class="pring"><svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="50" fill="none" stroke="rgba(243,241,236,.1)" stroke-width="8"/><circle class="pr" cx="60" cy="60" r="50" fill="none" stroke="#7C8BFF" stroke-width="8" stroke-linecap="round"/></svg></div>
      <div class="ptxt"><b>Squeeze ${sq} s</b> as the ring closes · <b>relax ${rl} s</b> as it opens</div>`;
    const pr = box.querySelector(".pr");
    pr.animate([{transform: "scale(1)", opacity: .55, offset: 0}, {transform: "scale(.62)", opacity: 1, offset: sq / T}, {transform: "scale(1)", opacity: .55, offset: 1}],
      {duration: T * 1000, iterations: Infinity, easing: "ease-in-out"});
    return box;
  }''')
rep('''<div class="nextup">${e && EMBED_VIDEO ? `<img alt="" src="${ytThumb(e.video)}">` : ""}''', '''<div class="nextup">${e && e.video && EMBED_VIDEO ? `<img alt="" src="${ytThumb(e.video)}">` : ""}''')
rep("</style>\n</head>", r""".vid.pace{display:grid;place-content:center;justify-items:center;gap:12px;aspect-ratio:16/9;background:radial-gradient(circle at 50% 40%,#151826,#08090C 70%);border-radius:18px;padding:16px}
.vid.pace .pring{width:min(46vw,180px);aspect-ratio:1}
.vid.pace svg{width:100%;height:100%}
.vid.pace .pr{transform-origin:60px 60px}
.vid.pace .ptxt{font-size:13.5px;color:rgba(243,241,236,.75);text-align:center;max-width:300px}
.vid.pace .ptxt b{color:#F3F1EC}
</style>
</head>""")

# builder: its own area; kept out of the default workout
rep('''const AREAS = ["Upper body", "Legs & glutes", "Core", "Back", "Your own"];''', '''const AREAS = ["Upper body", "Legs & glutes", "Core", "Back", "Pelvic floor", "Your own"];''')
rep('''  const AR = ["Upper body", "Legs & glutes", "Core", "Back"], idx''', '''  const AR = ["Upper body", "Legs & glutes", "Core", "Back", "Pelvic floor"], idx''')
rep('''  const lib = ROUTINE.map(r => { const o = full.find(x => x.id === r.id); return {...r, target: o ? o.target : r.target}; });''',
    '''  const lib = [...ROUTINE, ...EXTRA_LIB].map(r => { const o = full.find(x => x.id === r.id); return {...r, target: o ? o.target : r.target}; });''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
