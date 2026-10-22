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

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(0xFF123A26);
        getWindow().setNavigationBarColor(0xFF0D1611);

        root = new FrameLayout(this);
        root.setBackgroundColor(0xFF0D1611);
        web = new WebView(this);
        web.setBackgroundColor(0xFF0D1611);
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
        });

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
        if (backgroundSince > 0 && SystemClock.elapsedRealtime() - backgroundSince > RELOCK_AFTER_MS && AppLock.isAvailable(this)) {
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
        /** The tracker says a block has begun (ticked, timed, reps logged, workout started): stop its nag. */
        @JavascriptInterface public void blockStarted(String blockId) {
            if (Nag.isFive(blockId)) Nag.markStarted(getApplicationContext(), blockId);
        }
    }
}
