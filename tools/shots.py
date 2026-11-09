"""Render the app at phone width with sample data and save screenshots. Usage: python tools/shots.py [scenario ...]"""
import os, sys, subprocess, time, json
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "tools", "build", "shots")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
os.makedirs(OUT, exist_ok=True)

SEED = r"""<script>
(function(){
  const theme = "%THEME%", who = "%WHO%";
  localStorage.clear(); localStorage.setItem("ordo-theme", theme);
  const iso = d => d.getFullYear() + "-" + String(d.getMonth()+1).padStart(2,"0") + "-" + String(d.getDate()).padStart(2,"0");
  const ago = n => { const d = new Date(); d.setDate(d.getDate() - n); return iso(d); };
  const days = {};
  const G7 = {w_out:45, w_in:50, diet:true, water:3.8, alcohol:true, read:12, photo:true};
  for (let i = 11; i >= 1; i--) days[ago(i)] = {date: ago(i), done: who === "me" ? {wake:1,train:1,build:1,publish:1,connect:1,review:1} : {}, mins:{}, clock:{}, reps:{}, top3:["","",""], gratitude:"", goals: i === 7 ? {...G7, photo: false} : G7};
  days[ago(1)].top3 = ["Ship the client deck", "Film one video", "Call Ada"]; days[ago(1)].proud = "Finished both workouts before 9am";
  days[ago(1)].doDiff = "Phone stays out of the room until noon";
  days[ago(0)] = {date: ago(0), done: who === "me" ? {wake:1,train:1,build:1} : {}, mins:{}, clock:{wake:298}, reps:{wide_pushups:30, row_left:30}, top3:["","",""], gratitude:"", goals:{w_out:45, water:2.25, read:4, diet:true}, proud:"Closed a client"};
  const goals = [
    {id:"w_out", icon:"tree", name:"45-min outdoor workout", type:"time", target:45, unit:"min", step:5, workout:true},
    {id:"w_in", icon:"dumbbell", name:"45-min indoor workout", type:"time", target:45, unit:"min", step:5, workout:true},
    {id:"diet", icon:"plate", name:"Follow a healthy diet plan", type:"check"},
    {id:"water", icon:"glass", name:"Drink a gallon of water", type:"count", target:3.8, unit:"L", step:0.25},
    {id:"alcohol", icon:"nobottle", name:"No alcohol or cheat meals", type:"check"},
    {id:"read", icon:"book", name:"Read 10 pages of self-help", type:"count", target:10, unit:"pages", step:1},
    {id:"photo", icon:"camera", name:"Take a progress photo", type:"check"}];
  const settings = who === "blank" ? {dir:{}} : {dir:{}, plan:4, profile:{name: who === "me" ? "Chimdindu" : "Ada", schedule: who === "me", program:"75hard"}, goals,
    challenge:{name:"75 Hard", length:75, strict:true, start: ago(11)}, acct:{amount:5000, bar:"C", partner:"2348012345678", start: ago(9)}};
  if (who !== "blank") localStorage.setItem("builder-day-v2", JSON.stringify({days: who === "blank" ? {} : days, settings, reflections:{}}));
})();
</script>"""

SCEN = {
  "me-dark":     ("dark", "me", 3600, ""),
  "friend-dark": ("dark", "friend", 2600, ""),
  "friend-light":("light", "friend", 2600, ""),
  "board":       ("dark", "friend", 1700, "openBoard()"),
  "share":       ("dark", "friend", 900, "openShare(keyOf(new Date()))"),
  "welcome":     ("dark", "blank", 900, "onboarding('welcome')"),
  "program":     ("dark", "blank", 1100, "onboarding('program')"),
  "settings":    ("dark", "friend", 1500, "openSettings()"),
  "workout":     ("dark", "friend", 1300, "startWorkout(repDefs('train', keyOf(new Date())))"),
}

def shoot(name):
    theme, who, h, action = SCEN[name]
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    src = src.replace('<script src="firebase-config.js"></script>', "")
    src = src.replace("<head>\n", "<head>\n" + SEED.replace("%THEME%", theme).replace("%WHO%", who), 1)
    if action: src = src.replace("</body>", f"<script>setTimeout(()=>{{{action}}},900)</script></body>")
    open(os.path.join(ROOT, f"_s_{name}.html"), "w", encoding="utf-8").write(src)
    open(os.path.join(ROOT, f"_f_{name}.html"), "w").write(f'<!doctype html><body style="margin:0;background:#888"><iframe src="_s_{name}.html" style="width:390px;height:{h}px;border:0"></iframe></body>')
    png = os.path.join(OUT, name + ".png")
    subprocess.run([CHROME, "--headless=new", rf"--user-data-dir=C:\Users\DELL\AppData\Local\Temp\ordoshot_{name}", f"--window-size=500,{h}",
                    "--virtual-time-budget=7000", "--hide-scrollbars", "--screenshot=" + png, f"http://localhost:8790/_f_{name}.html"], capture_output=True, timeout=120)
    Image.open(png).crop((0, 0, 390, h)).save(png)
    for f in (f"_s_{name}.html", f"_f_{name}.html"): os.remove(os.path.join(ROOT, f))
    print("shot", png)

srv = subprocess.Popen(["python", "-m", "http.server", "8790"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
try:
    for n in (sys.argv[1:] or SCEN.keys()): shoot(n)
finally:
    srv.kill()
