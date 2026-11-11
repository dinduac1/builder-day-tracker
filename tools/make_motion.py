"""Builds the app's motion screens from ordo-anim.js (run after editing it):
   assets/loader.html (opening: "open"), assets/offline.html (reconnecting), and wires index.html / sw.js once."""
import os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
A = os.path.join(ROOT, "android", "app", "src", "main", "assets")
anim = open(os.path.join(ROOT, "ordo-anim.js"), encoding="utf-8").read()
RECONNECT = "charge"   # the user's pick for the Reconnecting screen: charge | flap | rise

open(os.path.join(A, "loader.html"), "w", encoding="utf-8", newline="\n").write(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@800&family=Geist+Mono:wght@500&display=swap">
<style>html,body{{margin:0;height:100%;background:#08090C;overflow:hidden}}main{{height:100%;display:grid;place-content:center}}</style></head>
<body><main id="m"></main><script>{anim}
ORDOAnim.mount(document.getElementById("m"), "open", {{size: 104}});</script></body></html>
''')

p = os.path.join(A, "offline.html"); s = open(p, encoding="utf-8").read()
s = re.sub(r'<svg class="ordo-load".*?</svg>\s*<div class="w">ORDO</div>', '<div id="anim"></div>', s, flags=re.S)
s = s.replace('<div class="s"><span id="s">Reconnecting</span><span class="ol-dots"></span></div>', '<div class="s" id="s"></div>')
if "ORDOAnim" not in s:
    s = s.replace("<script>\nvar SITE", "<script>" + anim + "\nORDOAnim.mount(document.getElementById('anim'), '" + RECONNECT + "', {size: 96});\n</script><script>\nvar SITE")
open(p, "w", encoding="utf-8", newline="\n").write(s)

P = os.path.join(ROOT, "index.html"); s = open(P, encoding="utf-8").read()
m = re.search(r'<div id="boot" aria-label="Loading ORDO">.*?</div></div>\n', s, re.S)
if m:
    s = s[:m.start()] + '<script src="ordo-anim.js"></script>\n<div id="boot" aria-label="Loading ORDO"><div id="bootAnim"></div></div>\n<script>window.ORDOAnim && ORDOAnim.mount(document.getElementById("bootAnim"), "sync", {size: 92});</script>\n' + s[m.end():]
open(P, "w", encoding="utf-8", newline="\n").write(s)

W = os.path.join(ROOT, "sw.js"); w = open(W, encoding="utf-8").read()
w = re.sub(r'<svg class="ordo-load".*?</svg>', '<div id="anim" style="justify-self:center"></div>', w, flags=re.S)
w = w.replace('<div class="s">Reconnecting<span class="ol-dots"></span></div>', '')
w = w.replace('<script>addEventListener("online",()=>location.reload())</script>', '<script src="ordo-anim.js"></script><script>window.ORDOAnim&&ORDOAnim.mount(document.getElementById("anim"),"' + RECONNECT + '",{size:96});addEventListener("online",()=>location.reload())</script>')
if '"ordo-anim.js"' not in w.split("const SHELL_HOSTS")[0]:
    w = w.replace('const CORE = ["./", ', 'const CORE = ["./", "ordo-anim.js", ')
w = re.sub(r'const CACHE = "ordo-v\d+"', 'const CACHE = "ordo-v4"', w)
open(W, "w", encoding="utf-8", newline="\n").write(w)
print("ok")
