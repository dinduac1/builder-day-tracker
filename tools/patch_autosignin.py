"""One-off: the app signs you back in by itself (silent Google sign-in) whenever its web session is missing,
e.g. after an update, so progress is there without logging in again. The loading screen covers it."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

J = os.path.join(ROOT, "android", "app", "src", "main", "java", "com", "builderday", "tracker", "TrackerActivity.java")
s = open(J, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)

rep('''                            String idToken = GoogleIdTokenCredential.createFrom(c.getData()).getIdToken();
                            js("window.__bdNativeSignIn && window.__bdNativeSignIn(" + JSONObject.quote(idToken) + ")");
                        } else {
                            jsError("Google didn't return an account.");''', '''                            String idToken = GoogleIdTokenCredential.createFrom(c.getData()).getIdToken();
                            rememberGoogle(true);
                            js("window.__bdNativeSignIn && window.__bdNativeSignIn(" + JSONObject.quote(idToken) + ")");
                        } else {
                            jsError("Google didn't return an account.");''')
rep('''    private void signOutOfGoogle() {''', '''    /** The person has signed in with Google in this app (cleared only when they sign out). */
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
        rememberGoogle(false);''')
rep('''        @JavascriptInterface public void signOut() { runOnUiThread(TrackerActivity.this::signOutOfGoogle); }''', '''        @JavascriptInterface public void signOut() { runOnUiThread(TrackerActivity.this::signOutOfGoogle); }
        @JavascriptInterface public void autoSignIn() { runOnUiThread(TrackerActivity.this::autoSignIn); }
        /** The page is signed in (covers people who signed in before this version existed). */
        @JavascriptInterface public void markSignedIn() { rememberGoogle(true); }''')
open(J, "w", encoding="utf-8", newline="\n").write(s)

P = os.path.join(ROOT, "index.html"); s = open(P, encoding="utf-8").read()
# the loading screen waits for the session to come back (max 7 s)
rep('''function bootDone(){
  const b = $("boot"); if (!b || b.classList.contains("out")) return;''', '''let bootWaitAuth = !!(NATIVE && NATIVE.autoSignIn);   // in the app, hold the loader while the session is restored
setTimeout(() => { bootWaitAuth = false; bootDone(); }, 7000);
function bootDone(){
  const b = $("boot"); if (!b || b.classList.contains("out") || bootWaitAuth) return;''')
rep('''    if (!u) {
      LS_KEY = "builder-day-v2"; lsLoad(); render();''', '''    if (!u && NATIVE && NATIVE.autoSignIn && !autoTried) {
      // the app was signed in before (e.g. this is an update): sign back in silently instead of asking
      autoTried = true;
      window.__ordoAutoSignInFailed = () => { autoFailed = true; showSignedOut(); };
      $("storeNote").textContent = "Signing you back in…";
      try { NATIVE.autoSignIn(); } catch(e) { showSignedOut(); }
      return;
    }
    if (!u) { showSignedOut(); return; }
    bootWaitAuth = false; bootDone();
    try { NATIVE && NATIVE.markSignedIn && NATIVE.markSignedIn(); } catch(e){}
    if (false) {''')
rep('''  window.__ordoSignIn = signIn;''', '''  window.__ordoSignIn = signIn;
  let autoTried = false, autoFailed = false;
  function showSignedOut(){
    bootWaitAuth = false; bootDone();
    if (auth.currentUser) return;
    authBox.innerHTML = "";
    LS_KEY = "builder-day-v2"; lsLoad(); render();
    if (!sessionStorage.getItem("ordo-local")) onboarding("welcome");
    $("storeNote").textContent = "Saved in this browser only. Sign in to sync across your devices.";
    const b = document.createElement("button"); b.className = "btn-g"; b.innerHTML = G_ICON + "<span>Sign in with Google</span>";
    b.onclick = signIn;
    authBox.appendChild(b);
  }''')
rep('''  window.__ordoSignOut = () => { auth.signOut(); if (NATIVE) NATIVE.signOut(); };''',
    '''  window.__ordoSignOut = () => { autoTried = true; auth.signOut(); if (NATIVE) NATIVE.signOut(); };''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
