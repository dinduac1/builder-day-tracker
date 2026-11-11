"""One-off: optional time cap (2/3/5 min) on rep exercises in the guided workout."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
rep("</style>\n</head>", """.capbar{display:grid;gap:6px;margin:-4px 0 4px}
.capbar .ct{display:flex;justify-content:space-between;align-items:baseline;font-family:var(--f-mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.capbar .ct b{font-family:var(--f-display);font-size:30px;font-weight:800;letter-spacing:.02em;color:var(--ink);cursor:pointer}
.capbar .tr{height:6px;border-radius:6px;background:var(--sunk);overflow:hidden}
.capbar .tr i{display:block;height:100%;background:var(--accent);border-radius:6px;transition:width 1s linear}
.capbar.late .tr i{background:var(--warn)}.capbar.late .ct b{color:var(--warn)}
.capbar.up .ct b{color:var(--warn)}
.capsel{display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.capsel button{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:6px 11px;font:inherit;font-size:12px;letter-spacing:0;cursor:pointer}
.capsel button.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
</style>
</head>""")
rep('''    ctrl.querySelector("#pgo").onclick = () => { beep(1320, .2); logCurrent(player.count); saveWorkoutLog(); nextExercise(true); };
  }
}''', '''    ctrl.querySelector("#pgo").onclick = () => { beep(1320, .2); logCurrent(player.count); saveWorkoutLog(); nextExercise(true); };
    // optional time cap: finish the set inside the clock, or it logs what you've got and moves on
    const sel = document.createElement("div"); sel.className = "capsel";
    sel.innerHTML = `Time cap ${[0, 120, 180, 300].map(c => `<button data-c="${c}" class="${c === repCap() ? "on" : ""}">${c ? fmtSec(c) : "Off"}</button>`).join("")}`;
    sel.querySelectorAll("button").forEach(b => b.onclick = () => { settings.repCap = Number(b.dataset.c); saveSettings(); showWork(); });
    ctrl.after(sel);
    const cap = repCap();
    if (cap && player.log[r.id] == null) {
      const bar = document.createElement("div"); bar.className = "capbar";
      bar.innerHTML = `<div class="ct"><span>Time left</span><b title="Tap to pause"></b></div><div class="tr"><i></i></div>`;
      big.before(bar);
      const t = bar.querySelector("b"), fill = bar.querySelector("i");
      let left = cap, grace = null, paused = false;
      const paintCap = () => {
        if (grace != null) { t.textContent = `Time's up · logging in ${grace}`; return; }
        t.textContent = fmtSec(left) + (paused ? " · paused" : "");
        fill.style.width = (left / cap * 100) + "%";
        bar.classList.toggle("late", left <= 30);
      };
      t.onclick = () => { if (grace == null) { paused = !paused; paintCap(); } };
      paintCap();
      player.tick = setInterval(() => {
        if (paused) return;
        if (grace != null) {
          grace--; paintCap();
          if (grace <= 0) { clearInterval(player.tick); beep(1320, .2); logCurrent(player.count); saveWorkoutLog(); nextExercise(true); }
          return;
        }
        left--; paintCap();
        if (left > 0 && left <= 3) beep(660, .08);
        if (left === 30) beep(880, .12);
        if (left <= 0) { beep(1320, .35); grace = 5; bar.classList.add("up"); paintCap(); }   // a moment to fix the count
      }, 1000);
    }
  }
}
const repCap = () => Number(settings.repCap) || 0;''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
