package com.builderday.tracker;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONObject;

/**
 * ORDO's lock screen (assets/lock.html): PIN keypad, password field, or the phone's own lock, with
 * fingerprint / face where allowed. RESULT_OK = unlocked. Extra "purpose": "unlock" (default) or "confirm"
 * (checking it's you before changing the lock).
 */
public class LockActivity extends Activity {
    static final String EXTRA_PURPOSE = "purpose";
    private WebView web;
    private boolean confirm;

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF08090C);
        getWindow().setNavigationBarColor(0xFF08090C);
        getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);   // no screenshots of the keypad
        confirm = "confirm".equals(getIntent().getStringExtra(EXTRA_PURPOSE));
        if (!AppLock.enabled(this)) { setResult(RESULT_OK); finish(); return; }
        web = new WebView(this);
        web.setBackgroundColor(0xFF08090C);
        web.getSettings().setJavaScriptEnabled(true);
        web.addJavascriptInterface(new Bridge(), "ORDOLock");
        setContentView(web);
        web.loadUrl("file:///android_asset/lock.html");
    }

    @Override
    public void onBackPressed() {
        if (confirm) { setResult(RESULT_CANCELED); finish(); }
        else moveTaskToBack(true);   // locked stays locked
    }

    private void unlocked() { setResult(RESULT_OK); finish(); overridePendingTransition(0, android.R.anim.fade_out); }
    private void js(String code) { if (web != null) web.evaluateJavascript(code, null); }

    private class Bridge {
        @JavascriptInterface public String info() {
            try {
                return new JSONObject(AppLock.info(LockActivity.this)).put("confirm", confirm)
                        .put("bioAllowed", AppLock.bioAllowed(LockActivity.this)).toString();
            } catch (Exception e) { return "{}"; }
        }
        @JavascriptInterface public String check(String secret) {
            String r = AppLock.check(LockActivity.this, secret);
            if (r.isEmpty()) runOnUiThread(LockActivity.this::unlocked);
            return r;
        }
        /** Fingerprint / face (PIN & password locks), or the full phone prompt (phone lock). */
        @JavascriptInterface public void biometric() {
            runOnUiThread(() -> {
                boolean device = AppLock.DEVICE.equals(AppLock.mode(LockActivity.this));
                AppLock.prompt(LockActivity.this, device,
                        device ? "Fingerprint, face, or your phone's PIN, pattern or password" : "Fingerprint or face",
                        ok -> { if (ok) unlocked(); else js("window.bioCancelled && bioCancelled()"); });
            });
        }
        /** Forgot the PIN / password: prove it's the phone's owner with the phone's own lock, then the ORDO lock is cleared. */
        @JavascriptInterface public void forgot() {
            runOnUiThread(() -> {
                if (!AppLock.deviceSecure(LockActivity.this)) {
                    js("window.forgotUnavailable && forgotUnavailable()");
                    return;
                }
                AppLock.prompt(LockActivity.this, true, "Use your phone's own lock to reset ORDO's", ok -> {
                    if (!ok) return;
                    AppLock.set(LockActivity.this, AppLock.OFF, null, 4, true);
                    android.widget.Toast.makeText(LockActivity.this, "App lock is off. Set a new one in Settings → App lock.", android.widget.Toast.LENGTH_LONG).show();
                    unlocked();
                });
            });
        }
        @JavascriptInterface public void cancel() { runOnUiThread(LockActivity.this::onBackPressed); }
    }
}
