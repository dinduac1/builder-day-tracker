package com.builderday.tracker;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
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
    private WebView splash;
    private String pendingOpen;                                // "chat" when opened from a chat notification
    private boolean pageReady;                                    // ORDO loading animation over the page while it loads
    private static final int RC_PICK = 7;
    private android.webkit.ValueCallback<Uri[]> pickCallback;   // profile photo picker
    private boolean picking = false;
    private Uri cameraUri;                                     // where the camera writes a progress photo
    private static final int RC_CAM = 8, RC_LOCK = 9, RC_CONFIRM = 12, RC_GAL = 13;
    private String[] pendingLock;                              // a lock change waiting for "confirm it's you"
    private android.webkit.PermissionRequest pendingCam;      // the page asked for camera / microphone; waiting on Android's prompt
    private String[] pendingRes;                           // the picker isn't "leaving the app": no relock

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
        if (state == null) {
            splash = new WebView(this);
            splash.setBackgroundColor(0xFF08090C);
            splash.setVerticalScrollBarEnabled(false);
            splash.loadUrl("file:///android_asset/loader.html");
            root.addView(splash, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            root.postDelayed(this::hideSplash, 12_000);   // never trap anyone behind it
        }
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
            @Override
            public android.webkit.WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest req) {
                return localMedia(req.getUrl());
            }
            @Override
            public void onPageFinished(WebView v, String url) {
                if (url != null && url.startsWith("about:")) hideSplash();          // offline screen has its own animation
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
            // the page asks for the camera (ORDO camera) or microphone (voice notes): ask Android, then let it have them
            @Override public void onPermissionRequest(android.webkit.PermissionRequest req) {
                runOnUiThread(() -> {
                    if (!siteHost().equals(req.getOrigin().getHost())) { req.deny(); return; }
                    java.util.List<String> res = new java.util.ArrayList<>(), need = new java.util.ArrayList<>();
                    for (String r : req.getResources()) {
                        String perm = android.webkit.PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r) ? android.Manifest.permission.CAMERA
                                : android.webkit.PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r) ? android.Manifest.permission.RECORD_AUDIO : null;
                        if (perm == null) continue;
                        res.add(r);
                        if (checkSelfPermission(perm) != android.content.pm.PackageManager.PERMISSION_GRANTED) need.add(perm);
                    }
                    if (res.isEmpty()) { req.deny(); return; }
                    if (need.isEmpty()) { req.grant(res.toArray(new String[0])); return; }
                    pendingCam = req; pendingRes = res.toArray(new String[0]); picking = true;
                    requestPermissions(need.toArray(new String[0]), RC_CAM);
                });
            }
            // <input type="file">: profile photos, gallery picks
            @Override public boolean onShowFileChooser(WebView v, android.webkit.ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (pickCallback != null) pickCallback.onReceiveValue(null);
                pickCallback = cb;
                boolean img = false, vid = false;
                for (String t : params.getAcceptTypes()) {
                    if (t == null) continue;
                    for (String one : t.split(",")) { one = one.trim(); if (one.startsWith("image")) img = true; if (one.startsWith("video")) vid = true; }
                }
                boolean multi = params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE;
                Intent launch = null;
                cameraUri = null;
                if (params.isCaptureEnabled() && (img || vid))                                  // "Take a photo" / "Record a video"
                    launch = vid && !img ? captureIntent(android.provider.MediaStore.ACTION_VIDEO_CAPTURE, ".mp4") : captureIntent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE, ".jpg");
                if (launch == null && (img || vid)) launch = galleryIntent(img, vid, multi);    // the phone's photo & video grid
                if (launch == null) launch = params.createIntent();
                try { picking = true; startActivityForResult(launch, RC_PICK); }
                catch (Exception e) { picking = false; pickCallback = null; cb.onReceiveValue(null); return false; }
                return true;
            }
        });

        // push token for crew alerts (stored for the page to register with the crew)
        try {
            com.google.firebase.messaging.FirebaseMessaging.getInstance().getToken().addOnSuccessListener(t ->
                    getSharedPreferences(CrewMessagingService.PREFS, MODE_PRIVATE).edit().putString(CrewMessagingService.KEY_TOKEN, t).apply());
        } catch (Throwable t) { Log.w(TAG, "push token unavailable", t); }

        pendingOpen = getIntent().getStringExtra("open");
        // requests made through the service worker reach the app here, not through the WebViewClient
        try {
            android.webkit.ServiceWorkerController.getInstance().setServiceWorkerClient(new android.webkit.ServiceWorkerClient() {
                @Override public android.webkit.WebResourceResponse shouldInterceptRequest(WebResourceRequest req) { return localMedia(req.getUrl()); }
            });
        } catch (Throwable t) { Log.w(TAG, "service worker client", t); }
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
    public void onRequestPermissionsResult(int rc, String[] perms, int[] results) {
        super.onRequestPermissionsResult(rc, perms, results);
        if (rc == RC_GAL) { js("window.__ordoGalleryPerm && window.__ordoGalleryPerm(" + JSONObject.quote(galleryAccess()) + ")"); return; }
        if (rc != RC_CAM || pendingCam == null) return;
        boolean all = results.length > 0;
        for (int r : results) if (r != android.content.pm.PackageManager.PERMISSION_GRANTED) all = false;
        if (all && pendingRes != null) pendingCam.grant(pendingRes); else pendingCam.deny();
        pendingCam = null;
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == RC_LOCK) { if (res == RESULT_OK) root.setVisibility(View.VISIBLE); return; }
        if (req == RC_CONFIRM) {
            if (res == RESULT_OK && pendingLock != null) applyLock(pendingLock);
            else reportLock("");
            pendingLock = null;
            return;
        }
        if (req != RC_PICK || pickCallback == null) return;
        Uri[] got = null;
        if (res == RESULT_OK && data != null) {
            if (data.getClipData() != null) {                       // several picked
                android.content.ClipData c = data.getClipData();
                got = new Uri[c.getItemCount()];
                for (int i = 0; i < got.length; i++) got[i] = c.getItemAt(i).getUri();
            } else if (data.getData() != null) got = new Uri[]{data.getData()};
        }
        if (res == RESULT_OK && (got == null || got.length == 0) && cameraUri != null) got = new Uri[]{cameraUri};   // came from the camera
        pickCallback.onReceiveValue(got);
        pickCallback = null;
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        String open = intent.getStringExtra("open");
        if (open != null) { pendingOpen = open; if (pageReady) deliverOpen(); }
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
        if (backgroundSince > 0 && SystemClock.elapsedRealtime() - backgroundSince > RELOCK_AFTER_MS && AppLock.enabled(this)) {
            root.setVisibility(View.INVISIBLE);   // nothing readable behind the lock screen
            picking = true;                       // coming back from the lock screen isn't "leaving the app"
            startActivityForResult(new Intent(this, LockActivity.class), RC_LOCK);
            overridePendingTransition(0, 0);
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
                            rememberGoogle(true);
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

    /** The person has signed in with Google in this app (cleared only when they sign out). */
    private void rememberGoogle(boolean on) { getSharedPreferences("auth", MODE_PRIVATE).edit().putBoolean("google", on).apply(); }

    /**
     * The page has no session (after an update, cleared storage, a new WebView): sign back in with the
     * Google account already used here, with no account picker. Tells the page if that isn't possible.
     */
    private void autoSignIn() {
        if (!getSharedPreferences("auth", MODE_PRIVATE).getBoolean("google", false)) { js("window.__ordoAutoSignInFailed && window.__ordoAutoSignInFailed()"); return; }
        com.google.android.libraries.identity.googleid.GetGoogleIdOption opt = new com.google.android.libraries.identity.googleid.GetGoogleIdOption.Builder()
                .setServerClientId(WEB_CLIENT_ID).setFilterByAuthorizedAccounts(true).setAutoSelectEnabled(true).build();
        GetCredentialRequest request = new GetCredentialRequest.Builder().addCredentialOption(opt).build();
        CredentialManager.create(this).getCredentialAsync(this, request, new CancellationSignal(), getMainExecutor(),
                new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                    @Override public void onResult(GetCredentialResponse response) {
                        Credential c = response.getCredential();
                        if (c instanceof CustomCredential && GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(c.getType())) {
                            String idToken = GoogleIdTokenCredential.createFrom(c.getData()).getIdToken();
                            js("window.__bdNativeSignIn && window.__bdNativeSignIn(" + JSONObject.quote(idToken) + ")");
                        } else js("window.__ordoAutoSignInFailed && window.__ordoAutoSignInFailed()");
                    }
                    @Override public void onError(GetCredentialException e) {
                        Log.w(TAG, "silent sign-in unavailable", e);
                        js("window.__ordoAutoSignInFailed && window.__ordoAutoSignInFailed()");
                    }
                });
    }

    private void signOutOfGoogle() {
        rememberGoogle(false);
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
        @JavascriptInterface public void autoSignIn() { runOnUiThread(TrackerActivity.this::autoSignIn); }
        /** The page is signed in (covers people who signed in before this version existed). */
        @JavascriptInterface public void markSignedIn() { rememberGoogle(true); }
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
        /** Every app on this phone that can send text (WhatsApp and WhatsApp Business separately), with icons. */
        @JavascriptInterface public String shareTargets() {
            try {
                android.content.pm.PackageManager pm = getPackageManager();
                Intent probe = new Intent(Intent.ACTION_SEND).setType("text/plain");
                org.json.JSONArray out = new org.json.JSONArray();
                java.util.Set<String> seen = new java.util.HashSet<>();
                for (android.content.pm.ResolveInfo r : pm.queryIntentActivities(probe, 0)) {
                    String pkg = r.activityInfo.packageName;
                    if (pkg.equals(getPackageName()) || !seen.add(pkg)) continue;   // one entry per app
                    String label = String.valueOf(pm.getApplicationLabel(r.activityInfo.applicationInfo));
                    if (pkg.equals("com.whatsapp.w4b") && !label.toLowerCase().contains("business")) label = "WhatsApp Business";
                    out.put(new org.json.JSONObject().put("pkg", pkg).put("label", label).put("icon", iconData(r.loadIcon(pm))));
                }
                return out.toString();
            } catch (Exception e) { return "[]"; }
        }
        /** Send straight to one app. WhatsApp (either one) opens the partner's chat when a number is given. */
        @JavascriptInterface public void shareTo(String pkg, String text, String phone) {
            runOnUiThread(() -> {
                Intent i = new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text).setPackage(pkg);
                if (phone != null && phone.matches("[0-9]{7,15}") && (pkg.equals("com.whatsapp") || pkg.equals("com.whatsapp.w4b")))
                    i.putExtra("jid", phone + "@s.whatsapp.net");
                try { startActivity(i); }
                catch (Exception e) { startActivity(Intent.createChooser(new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text), "Send with")); }
            });
        }
        /** Send text plus a photo (a data: URL) to one app; WhatsApp opens the partner's chat when a number is given. */
        @JavascriptInterface public void shareImageTo(String pkg, String text, String phone, String image) {
            runOnUiThread(() -> {
                Uri u = cacheImage(image, "report.jpg");
                Intent i = new Intent(Intent.ACTION_SEND).putExtra(Intent.EXTRA_TEXT, text);
                if (u != null) i.setType("image/jpeg").putExtra(Intent.EXTRA_STREAM, u).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                else i.setType("text/plain");
                Intent direct = new Intent(i).setPackage(pkg);
                if (phone != null && phone.matches("[0-9]{7,15}") && (pkg.equals("com.whatsapp") || pkg.equals("com.whatsapp.w4b")))
                    direct.putExtra("jid", phone + "@s.whatsapp.net");
                try { startActivity(direct); } catch (Exception e) { startActivity(Intent.createChooser(i, "Send with")); }
            });
        }
        /** Save a progress photo to the phone's gallery (Pictures/ORDO). Returns "" or what went wrong. */
        @JavascriptInterface public String savePhoto(String image, String name) {
            try {
                byte[] bytes = decodeData(image);
                if (bytes == null) return "No photo";
                if (Build.VERSION.SDK_INT >= 29) {
                    android.content.ContentValues v = new android.content.ContentValues();
                    v.put(android.provider.MediaStore.Images.Media.DISPLAY_NAME, name);
                    v.put(android.provider.MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                    v.put(android.provider.MediaStore.Images.Media.RELATIVE_PATH, "Pictures/ORDO");
                    Uri u = getContentResolver().insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
                    if (u == null) return "The gallery refused the file";
                    try (java.io.OutputStream o = getContentResolver().openOutputStream(u)) { o.write(bytes); }
                } else {
                    java.io.File dir = new java.io.File(android.os.Environment.getExternalStoragePublicDirectory(android.os.Environment.DIRECTORY_PICTURES), "ORDO");
                    dir.mkdirs();
                    java.io.File f = new java.io.File(dir, name);
                    try (java.io.FileOutputStream o = new java.io.FileOutputStream(f)) { o.write(bytes); }
                    android.media.MediaScannerConnection.scanFile(TrackerActivity.this, new String[]{f.getPath()}, null, null);
                }
                return "";
            } catch (Exception e) { return String.valueOf(e.getMessage()); }
        }
        /** The page has drawn its first screen: drop the loading animation. */
        @JavascriptInterface public void appReady() { runOnUiThread(() -> { hideSplash(); pageReady = true; deliverOpen(); }); }
        /** "all", "partial" (Android 14: only some photos allowed) or "none". */
        @JavascriptInterface public String galleryAccess() { return TrackerActivity.this.galleryAccess(); }
        @JavascriptInterface public void askGallery() {
            runOnUiThread(() -> {
                picking = true;
                if (Build.VERSION.SDK_INT >= 34) requestPermissions(new String[]{android.Manifest.permission.READ_MEDIA_IMAGES, android.Manifest.permission.READ_MEDIA_VIDEO, android.Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED}, RC_GAL);
                else if (Build.VERSION.SDK_INT >= 33) requestPermissions(new String[]{android.Manifest.permission.READ_MEDIA_IMAGES, android.Manifest.permission.READ_MEDIA_VIDEO}, RC_GAL);
                else requestPermissions(new String[]{android.Manifest.permission.READ_EXTERNAL_STORAGE}, RC_GAL);
            });
        }
        @JavascriptInterface public void openAppSettings() {
            runOnUiThread(() -> { picking = true; startActivity(new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName()))); });
        }
        /** Newest first. kind: "all" | "image" | "video". Each: {id, type, w, h, dur (s), size, date}. */
        @JavascriptInterface public String galleryPage(int offset, int limit, String kind) {
            org.json.JSONArray out = new org.json.JSONArray();
            try {
                Uri files = android.provider.MediaStore.Files.getContentUri("external");
                java.util.List<String> proj = new java.util.ArrayList<>(java.util.Arrays.asList("_id", "media_type", "mime_type", "width", "height", "date_added", "_size"));
                if (Build.VERSION.SDK_INT >= 29) proj.add("duration");
                Bundle args = new Bundle();
                args.putString(android.content.ContentResolver.QUERY_ARG_SQL_SELECTION, "image".equals(kind) ? "media_type=1" : "video".equals(kind) ? "media_type=3" : "media_type=1 OR media_type=3");
                args.putString(android.content.ContentResolver.QUERY_ARG_SQL_SORT_ORDER, "date_added DESC");
                args.putInt(android.content.ContentResolver.QUERY_ARG_LIMIT, Math.max(1, Math.min(200, limit)));
                args.putInt(android.content.ContentResolver.QUERY_ARG_OFFSET, Math.max(0, offset));
                try (android.database.Cursor c = getContentResolver().query(files, proj.toArray(new String[0]), args, null)) {
                    if (c != null) while (c.moveToNext()) {
                        boolean video = c.getInt(1) == 3;
                        org.json.JSONObject o = new org.json.JSONObject().put("id", c.getLong(0)).put("type", video ? "video" : "image")
                                .put("mime", c.getString(2)).put("w", c.getInt(3)).put("h", c.getInt(4)).put("date", c.getLong(5)).put("size", c.getLong(6));
                        if (proj.size() > 7) o.put("dur", c.getLong(7) / 1000.0);
                        out.put(o);
                    }
                }
            } catch (Exception e) { Log.w(TAG, "gallery", e); }
            return out.toString();
        }
        @JavascriptInterface public void notify(String title, String body) {
            Notifs.createChannels(getApplicationContext());
            Notifs.postCrew(getApplicationContext(), Math.abs(body.hashCode()) % 100000 + 10000, title, body);
        }
        @JavascriptInterface public void setScheduleEnabled(boolean on) { Scheduler.setEnabled(getApplicationContext(), on); }
        /** {mode, len, bio, bioAvailable, deviceSecure} */
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

    private void applyLock(String[] c) {
        reportLock(AppLock.set(this, c[0], c[1], Integer.parseInt(c[2]), Boolean.parseBoolean(c[3])));
    }
    private void reportLock(String error) {
        web.evaluateJavascript("window.__ordoLockChanged && window.__ordoLockChanged(" + AppLock.info(this) + "," + JSONObject.quote(error) + ")", null);
    }

    private String galleryAccess() {
        java.util.function.Predicate<String> ok = p -> checkSelfPermission(p) == android.content.pm.PackageManager.PERMISSION_GRANTED;
        if (Build.VERSION.SDK_INT >= 33) {
            if (ok.test(android.Manifest.permission.READ_MEDIA_IMAGES) || ok.test(android.Manifest.permission.READ_MEDIA_VIDEO)) return "all";
            if (Build.VERSION.SDK_INT >= 34 && ok.test(android.Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)) return "partial";
            return "none";
        }
        return ok.test(android.Manifest.permission.READ_EXTERNAL_STORAGE) ? "all" : "none";
    }

    /** /__local/thumb|file/image|video/<id> on our own site: answered from the phone's media store, never the network. */
    private android.webkit.WebResourceResponse localMedia(Uri u) {
        try {
            if (u == null || !siteHost().equals(u.getHost())) return null;
            java.util.List<String> p = u.getPathSegments();
            if (p.size() != 4 || !"__local".equals(p.get(0))) return null;
            boolean video = "video".equals(p.get(2));
            long id = Long.parseLong(p.get(3));
            Uri item = android.content.ContentUris.withAppendedId(video ? android.provider.MediaStore.Video.Media.EXTERNAL_CONTENT_URI : android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, id);
            java.util.Map<String, String> h = new java.util.HashMap<>();
            h.put("Cache-Control", "private, max-age=3600");
            android.content.ContentResolver cr = getContentResolver();
            if ("thumb".equals(p.get(1))) {
                android.graphics.Bitmap b;
                if (Build.VERSION.SDK_INT >= 29) b = cr.loadThumbnail(item, new android.util.Size(360, 360), null);
                else b = video ? android.provider.MediaStore.Video.Thumbnails.getThumbnail(cr, id, android.provider.MediaStore.Video.Thumbnails.MINI_KIND, null)
                               : android.provider.MediaStore.Images.Thumbnails.getThumbnail(cr, id, android.provider.MediaStore.Images.Thumbnails.MINI_KIND, null);
                if (b == null) return new android.webkit.WebResourceResponse("text/plain", "utf-8", 404, "Not Found", h, new java.io.ByteArrayInputStream(new byte[0]));
                java.io.ByteArrayOutputStream o = new java.io.ByteArrayOutputStream();
                b.compress(android.graphics.Bitmap.CompressFormat.JPEG, 82, o);
                return new android.webkit.WebResourceResponse("image/jpeg", null, 200, "OK", h, new java.io.ByteArrayInputStream(o.toByteArray()));
            }
            if ("file".equals(p.get(1))) {
                String mime = cr.getType(item);
                return new android.webkit.WebResourceResponse(mime != null ? mime : (video ? "video/mp4" : "image/jpeg"), null, 200, "OK", h, cr.openInputStream(item));
            }
        } catch (Exception e) { Log.w(TAG, "local media", e); }
        return null;
    }

    private void deliverOpen() {
        if (pendingOpen == null) return;
        js("window.__ordoOpen && window.__ordoOpen(" + JSONObject.quote(pendingOpen) + ")");
        pendingOpen = null;
    }

    private void hideSplash() {
        if (splash == null) return;
        WebView s = splash; splash = null;
        s.animate().alpha(0f).setDuration(280).withEndAction(() -> { root.removeView(s); s.destroy(); }).start();
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

    private static String iconData(android.graphics.drawable.Drawable d) {
        int n = 96;
        android.graphics.Bitmap b = android.graphics.Bitmap.createBitmap(n, n, android.graphics.Bitmap.Config.ARGB_8888);
        android.graphics.Canvas c = new android.graphics.Canvas(b);
        d.setBounds(0, 0, n, n); d.draw(c);
        java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
        b.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, out);
        return "data:image/png;base64," + android.util.Base64.encodeToString(out.toByteArray(), android.util.Base64.NO_WRAP);
    }

    /** Android's Photo Picker: every photo and video on the phone in a grid, no storage permission needed. */
    private Intent galleryIntent(boolean img, boolean vid, boolean multi) {
        boolean picker = Build.VERSION.SDK_INT >= 33;
        if (!picker && Build.VERSION.SDK_INT >= 30) {
            try { picker = android.os.ext.SdkExtensions.getExtensionVersion(Build.VERSION_CODES.R) >= 2; } catch (Throwable ignored) { }
        }
        if (picker) {
            Intent i = new Intent(android.provider.MediaStore.ACTION_PICK_IMAGES);
            if (img && !vid) i.setType("image/*"); else if (vid && !img) i.setType("video/*");
            if (multi) {
                int max = 30;
                try { max = Math.min(30, android.provider.MediaStore.getPickImagesMaxLimit()); } catch (Throwable ignored) { }
                i.putExtra(android.provider.MediaStore.EXTRA_PICK_IMAGES_MAX, max);
            }
            return i;
        }
        Intent i = new Intent(Intent.ACTION_GET_CONTENT).addCategory(Intent.CATEGORY_OPENABLE).setType(img && vid ? "*/*" : img ? "image/*" : "video/*");
        if (img && vid) i.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/*", "video/*"});
        if (multi) i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        return i;
    }

    private Intent captureIntent(String action, String ext) {
        Intent i = cameraIntent();
        if (i == null) return null;
        if (!android.provider.MediaStore.ACTION_IMAGE_CAPTURE.equals(action)) {
            try {
                java.io.File f = new java.io.File(new java.io.File(getCacheDir(), "photos"), "v" + System.currentTimeMillis() + ext);
                cameraUri = androidx.core.content.FileProvider.getUriForFile(this, getPackageName() + ".files", f);
                i = new Intent(action).putExtra(android.provider.MediaStore.EXTRA_OUTPUT, cameraUri)
                        .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                if (i.resolveActivity(getPackageManager()) == null) { cameraUri = null; return null; }
            } catch (Exception e) { cameraUri = null; return null; }
        }
        return i;
    }

    /** Camera intent that saves full-size into our cache (shared through FileProvider), or null if no camera app. */
    private Intent cameraIntent() {
        // declaring CAMERA means the phone's camera app also needs the grant
        if (checkSelfPermission(android.Manifest.permission.CAMERA) != android.content.pm.PackageManager.PERMISSION_GRANTED) { cameraUri = null; return null; }
        try {
            java.io.File dir = new java.io.File(getCacheDir(), "photos");
            if (!dir.exists()) dir.mkdirs();
            java.io.File[] old = dir.listFiles();
            if (old != null) for (java.io.File f : old) if (System.currentTimeMillis() - f.lastModified() > 86_400_000L) f.delete();
            java.io.File f = new java.io.File(dir, "p" + System.currentTimeMillis() + ".jpg");
            cameraUri = androidx.core.content.FileProvider.getUriForFile(this, getPackageName() + ".files", f);
            Intent i = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE)
                    .putExtra(android.provider.MediaStore.EXTRA_OUTPUT, cameraUri)
                    .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            return i.resolveActivity(getPackageManager()) != null ? i : null;
        } catch (Exception e) { Log.w(TAG, "camera", e); cameraUri = null; return null; }
    }

    private static byte[] decodeData(String dataUrl) {
        if (dataUrl == null) return null;
        int c = dataUrl.indexOf(',');
        if (!dataUrl.startsWith("data:") || c < 0) return null;
        return android.util.Base64.decode(dataUrl.substring(c + 1), android.util.Base64.DEFAULT);
    }

    /** Write a data: URL image into our cache and share it through FileProvider. */
    private Uri cacheImage(String dataUrl, String name) {
        try {
            byte[] b = decodeData(dataUrl);
            if (b == null) return null;
            java.io.File dir = new java.io.File(getCacheDir(), "photos");
            if (!dir.exists()) dir.mkdirs();
            java.io.File f = new java.io.File(dir, name);
            try (java.io.FileOutputStream o = new java.io.FileOutputStream(f)) { o.write(b); }
            return androidx.core.content.FileProvider.getUriForFile(this, getPackageName() + ".files", f);
        } catch (Exception e) { Log.w(TAG, "share image", e); return null; }
    }
}
