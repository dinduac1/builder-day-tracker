import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def r(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)
r('''  const mine = new Set(myTags());''', '''  const mine = new Set(myTags()); handles.add("crew"); mine.add("crew");''')
r('''    men.hidden = false; men.innerHTML = "";
    if (!list.length) {''', '''    men.hidden = false; men.innerHTML = "";
    if (others.length && (!q || "crew".startsWith(q) || "everyone".startsWith(q) || "all".startsWith(q))) {
      const b = document.createElement("button"); b.innerHTML = `<span class="av" style="background:var(--accent);color:#0A0C16">${others.length + 1}</span><span><b>Everyone in the crew</b><small>@crew</small></span>`;
      b.onmousedown = e => e.preventDefault();
      b.onclick = () => { const start = pre.length - m[2].length - 1; ta.value = ta.value.slice(0, start) + "@crew " + ta.value.slice(ta.selectionStart); ta.focus(); const c = start + 6; ta.setSelectionRange(c, c); men.hidden = true; mode(); };
      men.appendChild(b);
    }
    if (!list.length && men.childElementCount) return;
    if (!list.length) {''')
r('''    startRec(el).then(ok => { if (ok && (!pressing || Date.now() - downAt < 350 && !pressing)) setLock(el); });''',
  '''    startRec(el).then(ok => { if (ok && !pressing) setLock(el); });   // let go during a permission prompt: keep recording, locked''')
# the old menu is no longer used
i = s.index("function cameraSheet(el){"); j = s.index("\n}\n", i) + 3
s = s[:i] + s[j:]
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
