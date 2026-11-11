"""One-off: app lock choices (phone lock, ORDO PIN 4/6, ORDO password, optional fingerprint/face) with ORDO's lock screen,
and an App lock page in Settings."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
A = os.path.join(ROOT, "android", "app", "src", "main")
J = os.path.join(A, "java", "com", "builderday", "tracker")

def edit(path, pairs):
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (os.path.basename(path), s.count(a), a[:80])
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="\n").write(s)

edit(os.path.join(A, "AndroidManifest.xml"), [('''        <activity
            android:name=".WakeActivity"''', '''        <!-- ORDO's lock screen: PIN, password, or the phone's lock -->
        <activity
            android:name=".LockActivity"
            android:exported="false"
            android:excludeFromRecents="true"
            android:windowSoftInputMode="adjustResize" />

        <activity
            android:name=".WakeActivity"''')])

# StartActivity: hand unlocking to LockActivity
p = os.path.join(J, "StartActivity.java"); s = open(p, encoding="utf-8").read()
i = s.index("        if (!AppLock.enabled(this)) { onUnlocked(); return; }   // app lock switched off in Settings\n")
j = s.index("    @Override\n    protected void onActivityResult(int rc, int result, Intent data) {")
s = s[:i] + '''        if (!AppLock.enabled(this)) { onUnlocked(); return; }   // no app lock chosen
        unlocking = true;
        if (unlockButton != null) unlockButton.setVisibility(android.view.View.INVISIBLE);
        startActivityForResult(new Intent(this, LockActivity.class), RC_AUTH);
        overridePendingTransition(android.R.anim.fade_in, 0);
    }

''' + s[j:]
s = s.replace('sub.setText("Locked · use your fingerprint or screen lock");', 'sub.setText("Locked");')
open(p, "w", encoding="utf-8", newline="\n").write(s)

edit(os.path.join(J, "TrackerActivity.java"), [
    ('''        if (backgroundSince > 0 && SystemClock.elapsedRealtime() - backgroundSince > RELOCK_AFTER_MS && AppLock.enabled(this) && AppLock.isAvailable(this)) {
            root.setVisibility(View.INVISIBLE);   // nothing readable behind the prompt
            AppLock.prompt(this, ok -> {
                if (ok) root.setVisibility(View.VISIBLE);
                else moveTaskToBack(true);       // cancelled: leave the app locked
            });
        }''', '''        if (backgroundSince > 0 && SystemClock.elapsedRealtime() - backgroundSince > RELOCK_AFTER_MS && AppLock.enabled(this)) {
            root.setVisibility(View.INVISIBLE);   // nothing readable behind the lock screen
            picking = true;                       // coming back from the lock screen isn't "leaving the app"
            startActivityForResult(new Intent(this, LockActivity.class), RC_LOCK);
            overridePendingTransition(0, 0);
        }'''),
    ('''        super.onActivityResult(req, res, data);
        if (req != RC_PICK || pickCallback == null) return;''', '''        super.onActivityResult(req, res, data);
        if (req == RC_LOCK) { if (res == RESULT_OK) root.setVisibility(View.VISIBLE); return; }
        if (req == RC_CONFIRM) {
            if (res == RESULT_OK && pendingLock != null) applyLock(pendingLock);
            else reportLock("");
            pendingLock = null;
            return;
        }
        if (req != RC_PICK || pickCallback == null) return;'''),
    ('''    private static final int RC_CAM = 8;''', '''    private static final int RC_CAM = 8, RC_LOCK = 9, RC_CONFIRM = 12;
    private String[] pendingLock;                              // a lock change waiting for "confirm it's you"'''),
    ('''        /** "on", "off", or "unavailable" (no screen lock set on the phone). */
        @JavascriptInterface public String appLockState() {
            if (!AppLock.isAvailable(TrackerActivity.this)) return "unavailable";
            return AppLock.enabled(TrackerActivity.this) ? "on" : "off";
        }''', '''        /** {mode, len, bio, bioAvailable, deviceSecure} */
        @JavascriptInterface public String lockInfo() { return AppLock.info(TrackerActivity.this); }
        /** Change the lock. If one is on, the current one must be passed first. Result: window.__ordoLockChanged(info, error). */
        @JavascriptInterface public void setLock(String mode, String secret, int len, boolean bio) {
            runOnUiThread(() -> {
                String[] change = {mode, secret, String.valueOf(len), String.valueOf(bio)};
                if (AppLock.enabled(TrackerActivity.this)) {
                    pendingLock = change; picking = true;
                    startActivityForResult(new Intent(TrackerActivity.this, LockActivity.class).putExtra(LockActivity.EXTRA_PURPOSE, "confirm"), RC_CONFIRM);
                } else applyLock(change);
            });
        }'''),
    ('''        /** Switching the lock off needs the fingerprint / screen lock first; the page hears back via __ordoLockChanged. */
        @JavascriptInterface public void setAppLock(boolean on) {
            runOnUiThread(() -> {
                if (on) { AppLock.setEnabled(TrackerActivity.this, true); reportLock(); return; }
                AppLock.prompt(TrackerActivity.this, ok -> { if (ok) AppLock.setEnabled(TrackerActivity.this, false); reportLock(); });
            });
        }''', ""),
    ('''    private void reportLock() {
        String st = !AppLock.isAvailable(this) ? "unavailable" : AppLock.enabled(this) ? "on" : "off";
        web.evaluateJavascript("window.__ordoLockChanged && window.__ordoLockChanged('" + st + "')", null);
    }''', '''    private void applyLock(String[] c) {
        reportLock(AppLock.set(this, c[0], c[1], Integer.parseInt(c[2]), Boolean.parseBoolean(c[3])));
    }
    private void reportLock(String error) {
        web.evaluateJavascript("window.__ordoLockChanged && window.__ordoLockChanged(" + AppLock.info(this) + "," + JSONObject.quote(error) + ")", null);
    }'''),
])

# ---- web: App lock gets its own page
P = os.path.join(ROOT, "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)
i = s.index('    <div class="setgrp" id="stLockGrp" hidden>'); j = s.index("</div></div>", i) + len("</div></div>")
s = s[:i] + '''    <button class="setgrp setrow" id="stLockRow" hidden><span><h3>App lock</h3><span class="beat" id="stLockSum"></span></span><span class="chev" aria-hidden="true">›</span></button>''' + s[j:]
i = s.index("  if (NATIVE && NATIVE.appLockState) {"); j = s.index("  const th = (() => {", i)
s = s[:i] + '''  if (NATIVE && NATIVE.lockInfo) {
    o.querySelector("#stLockRow").hidden = false;
    o.querySelector("#stLockSum").textContent = lockSummary(JSON.parse(NATIVE.lockInfo() || "{}"));
    o.querySelector("#stLockRow").onclick = openLockPage;
  }
''' + s[j:]
rep("/* =========================================================== notification settings */", r'''/* =========================================================== app lock settings (the Android app) */
function lockSummary(L){
  return {off: "Off", device: "Phone's lock: fingerprint, face or phone PIN", pin: `ORDO ${L.len || 4}-digit PIN`, password: "ORDO password"}[L.mode] + (["pin", "password"].includes(L.mode) && L.bio && L.bioAvailable ? " + fingerprint/face" : "");
}
let lockDraft = null;
function openLockPage(){
  const o = ovl(), L = JSON.parse(NATIVE.lockInfo() || "{}");
  if (!lockDraft) lockDraft = {mode: L.mode, len: L.len || 4, bio: L.bio !== false};
  const D = lockDraft;
  const opts = [
    ["off", "Off", "Anyone holding your unlocked phone can open ORDO."],
    ["device", "Phone's lock", L.deviceSecure ? "Fingerprint, face, or your phone's PIN, pattern or password." : "Set a screen lock in your phone's settings to use this."],
    ["pin4", "4-digit PIN", "A PIN just for ORDO."],
    ["pin6", "6-digit PIN", "Harder to guess."],
    ["password", "Password", "Letters, numbers, anything. At least 6 characters."],
  ];
  const cur = D.mode === "pin" ? "pin" + D.len : D.mode;
  o.innerHTML = `<div class="in"><div class="bar"><span class="prog">Settings</span><button class="close">← Settings</button></div>
    <h2 class="exname">App lock</h2><p class="beat">How ORDO checks it's you when you open it, and again after 30 seconds away.</p>
    <div class="progs" id="lkOpts"></div><div id="lkSetup"></div><p class="beat" id="lkMsg"></p></div>`;
  o.querySelector(".close").onclick = () => { lockDraft = null; openSettings(); };
  const box = o.querySelector("#lkOpts");
  opts.forEach(([k, name, sub]) => {
    const c = document.createElement("button"); c.className = "prog-card" + (cur === k ? " on" : "");
    c.innerHTML = `<b></b><span></span><i></i>`; c.querySelector("b").textContent = name; c.querySelector("span").textContent = sub;
    const isNow = (L.mode === "pin" ? "pin" + L.len : L.mode) === k;
    c.querySelector("i").textContent = isNow ? "Current" : cur === k ? "Selected" : "";
    c.disabled = k === "device" && !L.deviceSecure;
    c.onclick = () => { D.mode = k.startsWith("pin") ? "pin" : k; if (k.startsWith("pin")) D.len = +k.slice(3); openLockPage(); };
    box.appendChild(c);
  });
  const st = o.querySelector("#lkSetup"), msg = o.querySelector("#lkMsg");
  const apply = (secret) => {
    window.__ordoLockChanged = (info, err) => { if (err) { msg.textContent = err; msg.style.color = "var(--warn)"; return; } lockDraft = null; toast("App lock: " + lockSummary(info) + "."); openSettings(); };
    NATIVE.setLock(D.mode, secret || "", D.len, !!D.bio);
  };
  const bioRow = () => {
    if (!L.bioAvailable) return null;
    const t = document.createElement("label"); t.className = "toggle"; t.innerHTML = `<span>Also unlock with fingerprint or face</span><input type="checkbox">`;
    const c = t.querySelector("input"); c.checked = D.bio; c.onchange = () => { D.bio = c.checked; };
    return t;
  };
  if (D.mode === "pin" || D.mode === "password") {
    const pin = D.mode === "pin";
    const g = document.createElement("div"); g.className = "setgrp";
    g.innerHTML = `<label class="fl">${pin ? `New ${D.len}-digit PIN` : "New password"}</label><input class="tx" type="password" id="lk1" ${pin ? `inputmode="numeric" maxlength="${D.len}" pattern="[0-9]*"` : `minlength="6" autocomplete="new-password"`}>
      <label class="fl">Type it again</label><input class="tx" type="password" id="lk2" ${pin ? `inputmode="numeric" maxlength="${D.len}" pattern="[0-9]*"` : `autocomplete="new-password"`}>
      ${pin ? "" : `<p class="beat">Don't use your crew code: everyone in your crew knows it.</p>`}`;
    const br = bioRow(); if (br) g.appendChild(br);
    const sv = document.createElement("button"); sv.className = "btn primary block"; sv.textContent = L.mode !== "off" ? "Confirm it's you, then save" : "Save";
    sv.onclick = () => {
      const a = g.querySelector("#lk1").value, b = g.querySelector("#lk2").value;
      msg.style.color = "var(--warn)";
      if (pin && !new RegExp(`^\\d{${D.len}}$`).test(a)) return msg.textContent = `Enter ${D.len} digits.`;
      if (!pin && a.length < 6) return msg.textContent = "Use at least 6 characters.";
      if (a !== b) return msg.textContent = "Those don't match. Type the same one twice.";
      if (pin && /^(\d)\1+$/.test(a)) return msg.textContent = "Pick something harder than one digit repeated.";
      msg.textContent = ""; apply(a);
    };
    g.appendChild(sv); st.appendChild(g);
  } else if (D.mode !== L.mode) {
    const sv = document.createElement("button"); sv.className = "btn primary block";
    sv.textContent = L.mode !== "off" ? "Confirm it's you, then save" : "Save";
    sv.onclick = () => apply("");
    st.appendChild(sv);
  } else if (D.mode === L.mode && (D.mode === "pin" || D.mode === "password")) {}
}

/* =========================================================== notification settings */''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
