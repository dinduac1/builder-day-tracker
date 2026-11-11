"""One-off: the ORDO loading animation (the icon's ring turning, ivory arc breathing, ultramarine segment leading),
used when the app opens, while the page boots, and on the offline / reconnecting screens."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "android", "app", "src", "main", "assets")

# circumference of r=17.5 is 110; ultramarine sits at 0–11, the ivory arc starts at 20 and breathes 34↔74
MARK = ('<svg class="ordo-load" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="15" fill="#111318"/>'
        '<circle cx="32" cy="32" r="17.5" fill="none" stroke="rgba(243,241,236,.08)" stroke-width="6.6"/>'
        '<g class="ol-rot"><g transform="rotate(-90 32 32)">'
        '<circle class="ol-iv" cx="32" cy="32" r="17.5" fill="none" stroke="#F3F1EC" stroke-width="6.6" stroke-linecap="round"/>'
        '<circle cx="32" cy="32" r="17.5" fill="none" stroke="#7C8BFF" stroke-width="6.6" stroke-linecap="round" stroke-dasharray="11 110"/>'
        '</g></g></svg>')
CSS = (".ordo-load{width:88px;height:88px;display:block;border-radius:21px;box-shadow:0 18px 50px rgba(0,0,0,.45)}"
       ".ordo-load .ol-rot{transform-origin:32px 32px;animation:ol-rot 1.5s linear infinite}"
       ".ordo-load .ol-iv{stroke-dasharray:54 110;stroke-dashoffset:-20;animation:ol-iv 1.5s ease-in-out infinite}"
       "@keyframes ol-rot{to{transform:rotate(-360deg)}}"
       "@keyframes ol-iv{0%,100%{stroke-dasharray:34 110}50%{stroke-dasharray:74 110}}"
       ".ol-word{font-family:'Big Shoulders Display',system-ui,sans-serif;font-weight:800;letter-spacing:.36em;font-size:15px;color:rgba(243,241,236,.62);margin-left:.36em}"
       ".ol-dots::after{content:'';animation:ol-dots 1.5s steps(4) infinite}"
       "@keyframes ol-dots{0%{content:''}25%{content:'.'}50%{content:'..'}75%{content:'...'}}"
       "@media (prefers-reduced-motion:reduce){.ordo-load .ol-rot{animation-duration:4s}.ordo-load .ol-iv{animation:none}}")

# 1) the app's loading screen (shown over the page while it loads)
open(os.path.join(ASSETS, "loader.html"), "w", encoding="utf-8", newline="\n").write(f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{{margin:0;height:100%;background:#08090C;overflow:hidden}}main{{height:100%;display:grid;place-content:center;justify-items:center;gap:22px}}{CSS}</style></head>
<body><main>{MARK}<div class="ol-word">ORDO</div></main></body></html>
''')

# 2) the app's offline screen: same mark, "Reconnecting"
p = os.path.join(ASSETS, "offline.html"); s = open(p, encoding="utf-8").read()
i = s.index("<svg"); j = s.index("</svg>") + 6
s = s[:i] + MARK + s[j:]
s = s.replace("svg{justify-self:center;width:84px;height:84px}", CSS + ".ordo-load{justify-self:center}")
s = s.replace('<div class="s" id="s"></div>', '<div class="s"><span id="s">Reconnecting</span><span class="ol-dots"></span></div>')
s = s.replace('document.getElementById("s").textContent = "Reconnecting…";', 'document.getElementById("s").textContent = "Connecting";')
open(p, "w", encoding="utf-8", newline="\n").write(s)

# 3) the website's offline fallback (service worker)
p = os.path.join(ROOT, "sw.js"); s = open(p, encoding="utf-8").read()
a = '<img src="icon-192.png" width="72" height="72" alt="" style="justify-self:center;border-radius:18px">'
assert a in s
s = s.replace(a, MARK.replace('class="ordo-load"', 'class="ordo-load" style="justify-self:center"'))
s = s.replace("button{justify-self:center;", CSS.replace("`", "") + ".s{font-family:monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#7C8BFF}button{justify-self:center;")
s = s.replace("<p>ORDO opens as soon as you're back online.</p>", "<p>ORDO opens as soon as you're back online.</p><div class=\"s\">Reconnecting<span class=\"ol-dots\"></span></div>")
s = s.replace('const CACHE = "ordo-v1";', 'const CACHE = "ordo-v2";')
open(p, "w", encoding="utf-8", newline="\n").write(s)

# 4) the page itself: boot screen until the first render (and fonts) are in
P = os.path.join(ROOT, "index.html"); s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
rep("</style>\n</head>", CSS + "\n#boot{position:fixed;inset:0;z-index:200;background:#08090C;display:grid;place-content:center;justify-items:center;gap:22px;transition:opacity .35s ease}\n#boot.out{opacity:0;pointer-events:none}\n</style>\n</head>")
rep('<body>\n', f'<body>\n<div id="boot" aria-label="Loading ORDO">{MARK}<div class="ol-word">ORDO</div></div>\n')
rep("/* ---------- boot ---------- */\n$(\"brandMark\").innerHTML = BRAND_SVG;", '''/* ---------- boot ---------- */
/** Fade the loading screen once the first render and the fonts are in (never longer than 2.5 s). */
function bootDone(){
  const b = $("boot"); if (!b || b.classList.contains("out")) return;
  b.classList.add("out"); setTimeout(() => b.remove(), 400);
  try { NATIVE && NATIVE.appReady && NATIVE.appReady(); } catch(e){}
}
Promise.race([document.fonts ? document.fonts.ready : Promise.resolve(), new Promise(r => setTimeout(r, 2500))]).then(() => requestAnimationFrame(() => setTimeout(bootDone, 120)));
$("brandMark").innerHTML = BRAND_SVG;''')
open(P, "w", encoding="utf-8", newline="\n").write(s)

# 5) the app shows loader.html on top until the page is ready
J = os.path.join(ROOT, "android", "app", "src", "main", "java", "com", "builderday", "tracker", "TrackerActivity.java")
s = open(J, encoding="utf-8").read()
rep('''    private long backgroundSince = 0;''', '''    private long backgroundSince = 0;
    private WebView splash;                                    // ORDO loading animation over the page while it loads''')
rep('''        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);''', '''        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        if (state == null) {
            splash = new WebView(this);
            splash.setBackgroundColor(0xFF08090C);
            splash.setVerticalScrollBarEnabled(false);
            splash.loadUrl("file:///android_asset/loader.html");
            root.addView(splash, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            root.postDelayed(this::hideSplash, 12_000);   // never trap anyone behind it
        }
        setContentView(root);''')
rep('''            // No connection and nothing cached: show ORDO's own offline screen, not Android's error page''', '''            @Override
            public void onPageFinished(WebView v, String url) {
                if (url != null && url.startsWith("about:")) hideSplash();          // offline screen has its own animation
            }
            // No connection and nothing cached: show ORDO's own offline screen, not Android's error page''')
rep('''        @JavascriptInterface public void notify(String title, String body) {''', '''        /** The page has drawn its first screen: drop the loading animation. */
        @JavascriptInterface public void appReady() { runOnUiThread(TrackerActivity.this::hideSplash); }
        @JavascriptInterface public void notify(String title, String body) {''')
rep('''    private void showOffline() {''', '''    private void hideSplash() {
        if (splash == null) return;
        WebView s = splash; splash = null;
        s.animate().alpha(0f).setDuration(280).withEndAction(() -> { root.removeView(s); s.destroy(); }).start();
    }

    private void showOffline() {''')
open(J, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
