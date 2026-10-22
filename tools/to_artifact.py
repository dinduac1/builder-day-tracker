"""Build the Claude-artifact copy of the tracker from index.html.

The artifact differs from the site in only a few ways:
- no <head>/<body> (the artifact viewer supplies the page skeleton), so the file starts at <title>
- no Firebase: data is kept in the artifact's own per-person store (claude.use("db"))
- no push reminders, and exercise videos link out to YouTube (artifacts can't embed other sites)

Usage: python tools/to_artifact.py [output.html]
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "index.html")
DST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "build", "builder-day-artifact.html")

s = open(SRC, encoding="utf-8").read()

def rep(old, new):
    global s
    assert old in s, "not found: " + old[:80]
    s = s.replace(old, new, 1)

s = s[s.index("<title>"):]
rep("</head>\n<body>\n", "")
rep("body{margin:0;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}\n", "")
s = s.rstrip()
assert s.endswith("</html>")
s = s[:s.rindex("</body>")].rstrip() + "\n"

s = re.sub(r'<script src="https://www\.gstatic\.com/firebasejs/[^"]+"></script>\n', "", s)
rep('<script src="firebase-config.js"></script>\n', "")
rep('\n      <div class="auth" id="auth"></div>', "")

rep("// Signed out: this browser's own copy. Signed in: a per-account cache, synced with Firestore.",
    "// Saved to the artifact's private per-person store; this browser keeps a copy for instant loads.")
rep('''  // users/{uid}/tracker/{day-YYYY-MM-DD | settings} — firestore.rules lets only that signed-in user read or write it
  const col = db.collection("users").doc(uid).collection("tracker");''',
    '''  const col = db.collection("data/users/" + uid);   // private to this viewer''')
rep('''e.code === "permission-denied" ? "Your account can't save here. Sign out and back in."''',
    '''e.code === "invalid_argument" ? "You can view this tracker but not save to it."''')

i = s.index("const G_ICON")
j = s.index("</script>", i)
s = s[:i] + '''(async () => {
  let db = null, user = null;
  try { [db, user] = await Promise.all([window.claude?.use?.("db"), window.claude?.use?.("user")]); } catch(e){}
  const uid = user ? await user.id().catch(() => null) : null;
  if (db && uid) {
    store = makeDbStore(db, uid);
    $("storeNote").textContent = "Saved to your account. Private to you, synced across devices.";
    store.subscribe();
  } else {
    $("storeNote").textContent = "Saved in this browser only.";
  }
})();
''' + s[j:]

rep("const EMBED_VIDEO = true;", "const EMBED_VIDEO = false;")
rep("const REMINDERS = true;", "const REMINDERS = false;   // service workers and push are unavailable inside artifacts")

os.makedirs(os.path.dirname(os.path.abspath(DST)), exist_ok=True)
open(DST, "w", encoding="utf-8", newline="\n").write(s)
m = re.search(r"<script>\n(.*?)</script>", s, re.S)
open(DST + ".check.js", "w", encoding="utf-8").write(m.group(1))
print("artifact written:", DST, len(s), "chars")
