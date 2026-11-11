package com.builderday.tracker;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import androidx.credentials.ClearCredentialStateRequest;
import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.exceptions.ClearCredentialException;
import androidx.credentials.exceptions.GetCredentialCancellationException;
import androidx.credentials.exceptions.GetCredentialException;

import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;

import org.json.JSONObject;

/**
 * The tracker, in the app's own screen (no Chrome).
 * - Loads the live site, so website updates arrive without reinstalling.
 * - Google sign-in happens natively (Android's account picker); the ID token is handed to the page,
 *   which signs into the same Firebase account. (Google blocks its web sign-in inside app web views.)
 * - Locks again with fingerprint / screen lock after the app has been in the background.
 */
public class TrackerActivity extends Activity {
    private static final String TAG = "BuilderDay";
    /** Firebase project's Google sign-in web client (Firebase console → Authentication → Google). */
    private static final String WEB_CLIENT_ID = "382000465773-5ns208p1o1rpq1psg5nvn5gafkqhabh8.apps.googleusercontent.com";
    private static final long RELOCK_AFTER_MS = 30_000;   // short trips (notification shade, a quick reply) don't relock

    private WebView web;
    private FrameLayout root;
    private View fullscreenView;
    private WebChromeClient.CustomViewCallback fullscreenCallback;
    private long backgroundSince = 0;
    private static final int RC_PICK = 7;
    private android.webkit.ValueCallback<Uri[]> pickCallback;   // profile photo picker
    private boolean picking = false;                           // the picker isn't "leaving the app": no relock

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF08090C);
        getWindow().setNavigationBarColor(0xFF08090C);

        root = new FrameLayout(this);
        root.setBackgroundColor(0xFF08090C);
        web = new WebView(this);
        web.setBackgroundColor(0xFF08090C);
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);

        WebSettings ws = web.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setMediaPlaybackRequiresUserGesture(false);   // muted, looping exercise demos
        ws.setUserAgentString(ws.getUserAgentString() + " BuilderDayApp/" + BuildConfigInfo.VERSION);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, true);   // YouTube embeds

        web.addJavascriptInterface(new Bridge(), "BuilderDayNative");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
                Uri u = req.getUrl();
                if (siteHost().equals(u.getHost())) return false;     // stay in the app
                if (!req.isForMainFrame()) return false;
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) { }
                return true;                                          // other sites open in their own app/browser
            }
            // No connection and nothing cached: show ORDO's own offline screen, not Android's error page
            @Override
            public void onReceivedError(WebView v, WebResourceRequest req, android.webkit.WebResourceError err) {
                if (req.isForMainFrame()) showOffline();
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            // full-screen video
            @Override public void onShowCustomView(View view, CustomViewCallback cb) {
                if (fullscreenView != null) { cb.onCustomViewHidden(); return; }
                fullscreenView = view; fullscreenCallback = cb;
                root.addView(view, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
                view.setBackgroundColor(Color.BLACK);
            }
            @Override public void onHideCustomView() { exitFullscreen(); }
            // <input type="file">: profile photos
            @Override public boolean onShowFileChooser(WebView v, android.webkit.ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (pickCallback != null) pickCallback.onReceiveValue(null);
                pickCallback = cb;
                try { picking = true; startActivityForResult(params.createIntent(), RC_PICK); }
                catch (Exception e) { picking = false; pickCallback = null; cb.onReceiveValue(null); return false; }
                return true;
            }
        });

        // push token for crew alerts (stored for the page to register with the crew)
        try {
            com.google.firebase.messaging.FirebaseMessaging.getInstance().getToken().addOnSuccessListener(t ->
                    getSharedPreferences(CrewMessagingService.PREFS, MODE_PRIVATE).edit().putString(CrewMessagingService.KEY_TOKEN, t).apply());
        } catch (Throwable t) { Log.w(TAG, "push token unavailable", t); }

        if (state != null) web.restoreState(state);
        else web.loadUrl(getString(R.string.site_url));
    }

    private String siteHost() { return Uri.parse(getString(R.string.site_url)).getHost(); }

    private void exitFullscreen() {
        if (fullscreenView == null) return;
        root.removeView(fullscreenView);
        fullscreenView = null;
        if (fullscreenCallback != null) fullscreenCallback.onCustomViewHidden();
        fullscreenCallback = null;
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req != RC_PICK || pickCallback == null) return;
        pickCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(res, data));
        pickCallback = null;
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
    }

    /* ---------- Back: video full screen → page's own back (closes guides / asks before leaving a workout) → leave ---------- */
    @Override
    public void onBackPressed() {
        if (fullscreenView != null) { exitFullscreen(); return; }
        if (web.canGoBack()) { web.goBack(); return; }
        super.onBackPressed();
    }

    /* ---------- relock after time away ---------- */
    @Override
    protected void onStop() {
        super.onStop();
        backgroundSince = SystemClock.elapsedRealtime();
    }

    @Override
    protected void onRestart() {
        super.onRestart();
        if (picking) { picking = false; backgroundSince = 0; return; }
        if (backgroundSince > 0 && SystemClock.elapsedRealtime() - backgroundSince > RELOCK_AFTER_MS && AppLock.enabled(this) && AppLock.isAvailable(this)) {
            root.setVisibility(View.INVISIBLE);   // nothing readable behind the prompt
            AppLock.prompt(this, ok -> {
                if (ok) root.setVisibility(View.VISIBLE);
                else moveTaskToBack(true);       // cancelled: leave the app locked
            });
        }
        backgroundSince = 0;
    }

    @Override
    protected void onResume() { super.onResume(); web.onResume(); }

    @Override
    protected void onPause() { web.onPause(); super.onPause(); }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onDestroy() {
        if (web != null) { web.destroy(); web = null; }
        super.onDestroy();
    }

    /* ---------- native Google sign-in ---------- */
    private void signInWithGoogle() {
        GetSignInWithGoogleOption option = new GetSignInWithGoogleOption.Builder(WEB_CLIENT_ID).build();
        GetCredentialRequest request = new GetCredentialRequest.Builder().addCredentialOption(option).build();
        CredentialManager.create(this).getCredentialAsync(this, request, new CancellationSignal(), getMainExecutor(),
                new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                    @Override public void onResult(GetCredentialResponse response) {
                        Credential c = response.getCredential();
                        if (c instanceof CustomCredential && GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(c.getType())) {
                            String idToken = GoogleIdTokenCredential.createFrom(c.getData()).getIdToken();
                            js("window.__bdNativeSignIn && window.__bdNativeSignIn(" + JSONObject.quote(idToken) + ")");
                        } else {
                            jsError("Google didn't return an account.");
                        }
                    }
                    @Override public void onError(GetCredentialException e) {
                        Log.w(TAG, "Google sign-in failed", e);
                        if (e instanceof GetCredentialCancellationException) return;   // closed the picker
                        jsError("Google sign-in didn't work: " + e.getMessage());
                    }
                });
    }

    private void signOutOfGoogle() {
        CredentialManager.create(this).clearCredentialStateAsync(new ClearCredentialStateRequest(), new CancellationSignal(),
                getMainExecutor(), new CredentialManagerCallback<Void, ClearCredentialException>() {
                    @Override public void onResult(Void v) { }
                    @Override public void onError(ClearCredentialException e) { Log.w(TAG, "clear credentials failed", e); }
                });
    }

    private void js(String code) { if (web != null) web.evaluateJavascript(code, null); }

    private void jsError(String msg) {
        js("window.__bdNativeSignInError && window.__bdNativeSignInError(" + JSONObject.quote(msg) + ")");
    }

    /** Methods the page can call as window.BuilderDayNative.*. Runs off the UI thread, so hop back to it. */
    private class Bridge {
        @JavascriptInterface public void signInWithGoogle() { runOnUiThread(TrackerActivity.this::signInWithGoogle); }
        @JavascriptInterface public void signOut() { runOnUiThread(TrackerActivity.this::signOutOfGoogle); }
        @JavascriptInterface public void keepAwake(boolean on) {
            runOnUiThread(() -> {
                if (on) getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            });
        }
        @JavascriptInterface public void toast(String s) {
            runOnUiThread(() -> Toast.makeText(TrackerActivity.this, s, Toast.LENGTH_SHORT).show());
        }
        @JavascriptInterface public String version() { return BuildConfigInfo.VERSION; }
        /** Android's own share sheet: any app on the phone. */
        @JavascriptInterface public void share(String text, String subject) {
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text).putExtra(Intent.EXTRA_SUBJECT, subject);
                startActivity(Intent.createChooser(i, "Send your report"));
            });
        }
        @JavascriptInterface public void notify(String title, String body) {
            Notifs.createChannels(getApplicationContext());
            Notifs.postCrew(getApplicationContext(), Math.abs(body.hashCode()) % 100000 + 10000, title, body);
        }
        @JavascriptInterface public void setScheduleEnabled(boolean on) { Scheduler.setEnabled(getApplicationContext(), on); }
        /** "on", "off", or "unavailable" (no screen lock set on the phone). */
        @JavascriptInterface public String appLockState() {
            if (!AppLock.isAvailable(TrackerActivity.this)) return "unavailable";
            return AppLock.enabled(TrackerActivity.this) ? "on" : "off";
        }
        /** Switching the lock off needs the fingerprint / screen lock first; the page hears back via __ordoLockChanged. */
        @JavascriptInterface public void setAppLock(boolean on) {
            runOnUiThread(() -> {
                if (on) { AppLock.setEnabled(TrackerActivity.this, true); reportLock(); return; }
                AppLock.prompt(TrackerActivity.this, ok -> { if (ok) AppLock.setEnabled(TrackerActivity.this, false); reportLock(); });
            });
        }
        @JavascriptInterface public String notifPrefs() { return NotifPrefs.json(getApplicationContext()); }
        @JavascriptInterface public void setNotif(String key, boolean on) {
            android.content.Context c = getApplicationContext();
            NotifPrefs.set(c, key, on);
            if (key.equals("all") || key.equals("block:wake") || key.equals("wake")) Scheduler.scheduleAll(c);
        }
        @JavascriptInterface public void setNotifSound(String key, String sound) {
            android.content.Context c = getApplicationContext();
            NotifPrefs.setSound(c, key, sound);
            Notifs.createChannels(c);
            NotifPrefs.preview(c, sound);
        }
        @JavascriptInterface public void previewSound(String sound) { NotifPrefs.preview(getApplicationContext(), sound); }
        @JavascriptInterface public void setRoutine(String json) {
            android.content.Context c = getApplicationContext();
            Schedule.save(c, json);
            Notifs.createChannels(c);
            Scheduler.scheduleAll(c);
        }
        @JavascriptInterface public String fcmToken() {
            return getSharedPreferences(CrewMessagingService.PREFS, MODE_PRIVATE).getString(CrewMessagingService.KEY_TOKEN, "");
        }
        /** The tracker says a block has begun (ticked, timed, reps logged, workout started): stop its nag. */
        @JavascriptInterface public void blockStarted(String blockId) {
            if (Nag.isFive(blockId)) Nag.markStarted(getApplicationContext(), blockId);
        }
    }

    private void reportLock() {
        String st = !AppLock.isAvailable(this) ? "unavailable" : AppLock.enabled(this) ? "on" : "off";
        web.evaluateJavascript("window.__ordoLockChanged && window.__ordoLockChanged('" + st + "')", null);
    }

    private void showOffline() {
        try (java.io.InputStream in = getAssets().open("offline.html")) {
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[4096]; int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            String html = out.toString("UTF-8").replace("__SITE__", getString(R.string.site_url));
            web.loadDataWithBaseURL("about:blank", html, "text/html", "utf-8", null);
        } catch (java.io.IOException e) { Log.w(TAG, "offline page", e); }
    }
}
