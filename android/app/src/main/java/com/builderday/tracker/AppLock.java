package com.builderday.tracker;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.Build;
import android.os.CancellationSignal;
import android.os.SystemClock;

import org.json.JSONObject;

import java.security.MessageDigest;
import java.security.SecureRandom;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * ORDO's app lock, chosen in Settings → App lock:
 *   off       no lock
 *   device    the phone's own lock: fingerprint, face, or the phone's PIN / pattern / password
 *   pin       an ORDO PIN (4 or 6 digits)
 *   password  an ORDO password
 * PIN and password can also allow fingerprint / face as a shortcut ("bio").
 * Secrets are never stored: only a salted PBKDF2 hash. Wrong guesses lock entry for a while, longer each time.
 */
final class AppLock {
    interface Result { void done(boolean unlocked); }

    static final String OFF = "off", DEVICE = "device", PIN = "pin", PASSWORD = "password";
    private static final int ITER = 120_000, FREE_TRIES = 5;

    private static SharedPreferences p(Context ctx) { return ctx.getSharedPreferences("lock", Context.MODE_PRIVATE); }

    static String mode(Context ctx) {
        SharedPreferences sp = p(ctx);
        String m = sp.getString("mode", null);
        if (m == null) m = sp.getBoolean("on", true) ? DEVICE : OFF;   // before lock choices existed
        if (DEVICE.equals(m) && !deviceSecure(ctx)) return OFF;          // nothing to check against
        return m;
    }
    static boolean enabled(Context ctx) { return !OFF.equals(mode(ctx)); }
    static int pinLength(Context ctx) { return p(ctx).getInt("len", 4); }
    static boolean bioAllowed(Context ctx) { return p(ctx).getBoolean("bio", true) && bioAvailable(ctx); }

    static boolean deviceSecure(Context ctx) {
        KeyguardManager km = ctx.getSystemService(KeyguardManager.class);
        return km != null && km.isDeviceSecure() && Build.VERSION.SDK_INT >= 29;
    }
    /** Fingerprint or face enrolled and usable. */
    static boolean bioAvailable(Context ctx) {
        if (Build.VERSION.SDK_INT < 30) return Build.VERSION.SDK_INT >= 29 && ctx.getSystemService(BiometricManager.class).canAuthenticate() == BiometricManager.BIOMETRIC_SUCCESS;
        return ctx.getSystemService(BiometricManager.class).canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_WEAK) == BiometricManager.BIOMETRIC_SUCCESS;
    }
    /** Kept for older callers: is there anything the phone itself can check? */
    static boolean isAvailable(Context ctx) { return deviceSecure(ctx); }

    static String info(Context ctx) {
        try {
            return new JSONObject().put("mode", mode(ctx)).put("len", pinLength(ctx)).put("bio", p(ctx).getBoolean("bio", true))
                    .put("bioAvailable", bioAvailable(ctx)).put("deviceSecure", deviceSecure(ctx)).toString();
        } catch (Exception e) { return "{}"; }
    }

    /** Apply a new choice. For PIN / password, secret is what the person typed (only its hash is kept). */
    static String set(Context ctx, String mode, String secret, int len, boolean bio) {
        SharedPreferences.Editor e = p(ctx).edit().remove("on").putBoolean("bio", bio).putInt("fails", 0).putLong("until", 0);
        if (PIN.equals(mode)) {
            if (secret == null || !secret.matches("[0-9]{" + len + "}") || (len != 4 && len != 6)) return "The PIN must be " + len + " digits.";
            e.putInt("len", len);
        } else if (PASSWORD.equals(mode)) {
            if (secret == null || secret.length() < 6) return "Use at least 6 characters.";
        } else if (DEVICE.equals(mode)) {
            if (!deviceSecure(ctx)) return "Set a screen lock in your phone's settings first.";
        } else if (!OFF.equals(mode)) return "Unknown lock.";
        if (PIN.equals(mode) || PASSWORD.equals(mode)) {
            byte[] salt = new byte[16]; new SecureRandom().nextBytes(salt);
            e.putString("salt", hex(salt)).putString("hash", hash(secret, salt));
        } else e.remove("salt").remove("hash");
        e.putString("mode", mode).apply();
        return "";
    }

    /** Seconds to wait before another try is allowed (0 = go ahead). */
    static long waitSeconds(Context ctx) {
        long until = p(ctx).getLong("until", 0), now = SystemClock.elapsedRealtime();
        if (until > now + 3_600_000L) until = 0;   // phone rebooted: elapsed clock reset
        return until > now ? (until - now + 999) / 1000 : 0;
    }

    /** Check a PIN / password. "" = right, "wait:N" = locked out for N seconds, else a message. */
    static String check(Context ctx, String secret) {
        long w = waitSeconds(ctx);
        if (w > 0) return "wait:" + w;
        SharedPreferences sp = p(ctx);
        String salt = sp.getString("salt", null), want = sp.getString("hash", null);
        if (salt == null || want == null) return "";
        if (MessageDigest.isEqual(hash(secret == null ? "" : secret, unhex(salt)).getBytes(), want.getBytes())) {
            sp.edit().putInt("fails", 0).putLong("until", 0).apply();
            return "";
        }
        int fails = sp.getInt("fails", 0) + 1;
        SharedPreferences.Editor e = sp.edit().putInt("fails", fails);
        if (fails >= FREE_TRIES && fails % FREE_TRIES == 0) {
            long secs = Math.min(900, 30L << Math.min(5, fails / FREE_TRIES - 1));   // 30 s, 60 s, 2 min … up to 15 min
            e.putLong("until", SystemClock.elapsedRealtime() + secs * 1000);
            e.apply();
            return "wait:" + secs;
        }
        e.apply();
        int left = FREE_TRIES - fails % FREE_TRIES;
        return (PIN.equals(mode(ctx)) ? "Wrong PIN." : "Wrong password.") + (left <= 2 ? " " + left + " more " + (left == 1 ? "try" : "tries") + " before a pause." : "");
    }

    /**
     * The system prompt. allowDevice = the phone's PIN/pattern/password may be used too (the "device" lock,
     * and "Forgot your PIN?"); otherwise fingerprint / face only.
     */
    static void prompt(Activity a, boolean allowDevice, String subtitle, Result result) {
        if (Build.VERSION.SDK_INT < 29) { result.done(false); return; }
        BiometricPrompt.Builder b = new BiometricPrompt.Builder(a).setTitle("Unlock ORDO").setSubtitle(subtitle);
        if (Build.VERSION.SDK_INT >= 30) {
            b.setAllowedAuthenticators(allowDevice ? BiometricManager.Authenticators.BIOMETRIC_WEAK | BiometricManager.Authenticators.DEVICE_CREDENTIAL
                    : BiometricManager.Authenticators.BIOMETRIC_WEAK);
            if (!allowDevice) b.setNegativeButton("Use " + (PIN.equals(mode(a)) ? "PIN" : "password"), a.getMainExecutor(), (d, w) -> result.done(false));
        } else if (allowDevice) b.setDeviceCredentialAllowed(true);
        else b.setNegativeButton("Cancel", a.getMainExecutor(), (d, w) -> result.done(false));
        b.build().authenticate(new CancellationSignal(), a.getMainExecutor(), new BiometricPrompt.AuthenticationCallback() {
            @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult r) { result.done(true); }
            @Override public void onAuthenticationError(int code, CharSequence msg) { result.done(false); }
        });
    }

    private static String hash(String secret, byte[] salt) {
        try {
            SecretKeyFactory f = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            return hex(f.generateSecret(new PBEKeySpec(secret.toCharArray(), salt, ITER, 256)).getEncoded());
        } catch (Exception e) { throw new RuntimeException(e); }
    }
    private static String hex(byte[] b) { StringBuilder s = new StringBuilder(); for (byte x : b) s.append(String.format("%02x", x)); return s.toString(); }
    private static byte[] unhex(String h) { byte[] b = new byte[h.length() / 2]; for (int i = 0; i < b.length; i++) b[i] = (byte) Integer.parseInt(h.substring(2 * i, 2 * i + 2), 16); return b; }

    private AppLock() {}
}
