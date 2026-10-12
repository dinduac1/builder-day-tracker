package com.builderday.tracker;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.Context;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.Build;
import android.os.CancellationSignal;

/** Fingerprint / face, falling back to the phone's PIN, pattern or password. */
final class AppLock {
    interface Result { void done(boolean unlocked); }

    /** True when the phone has a screen lock to check against (and Android can show the prompt). */
    static boolean isAvailable(Context ctx) {
        KeyguardManager km = ctx.getSystemService(KeyguardManager.class);
        return km != null && km.isDeviceSecure() && Build.VERSION.SDK_INT >= 29;
    }

    static void prompt(Activity a, Result result) {
        if (!isAvailable(a)) { result.done(true); return; }
        BiometricPrompt.Builder b = new BiometricPrompt.Builder(a)
                .setTitle("Unlock Builder Day")
                .setSubtitle("Fingerprint, face, or your phone's PIN, pattern or password");
        if (Build.VERSION.SDK_INT >= 30) {
            b.setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_WEAK | BiometricManager.Authenticators.DEVICE_CREDENTIAL);
        } else {
            b.setDeviceCredentialAllowed(true);
        }
        b.build().authenticate(new CancellationSignal(), a.getMainExecutor(), new BiometricPrompt.AuthenticationCallback() {
            @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult r) { result.done(true); }
            @Override public void onAuthenticationError(int code, CharSequence msg) { result.done(false); }
        });
    }

    private AppLock() {}
}
