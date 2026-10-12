package com.builderday.tracker;

import android.Manifest;
import android.app.Activity;
import android.app.AlarmManager;
import android.app.AlertDialog;
import android.app.NotificationManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.util.Log;
import android.view.Gravity;
import android.widget.TextView;
import android.widget.Toast;

import androidx.browser.customtabs.CustomTabColorSchemeParams;
import androidx.browser.trusted.TrustedWebActivityIntentBuilder;

import com.google.androidbrowserhelper.trusted.TwaLauncher;

import java.io.PrintWriter;
import java.io.StringWriter;

/**
 * App entry point and the tracker's host.
 * 1. Asks once for what reminders need: notifications, then (if the phone requires it) exact alarms and the
 *    full-screen wake-up screen.
 * 2. Schedules every reminder.
 * 3. Opens the tracker full screen in Chrome (Trusted Web Activity), launched directly from here.
 *    (The library's own LauncherActivity relaunches itself into a new task when it isn't the first screen,
 *    and on HyperOS that relaunch quits before Chrome starts.)
 * Nothing here may crash the app: failures are shown with a way to keep going, and a crash anywhere else
 * is saved and shown on the next launch.
 */
public class StartActivity extends Activity {
    private static final int RC_NOTIF = 10;
    private static final String TAG = "BuilderDay";
    private SharedPreferences prefs;
    private TwaLauncher launcher;
    private boolean notifAsked, launched, showingProblem;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("setup", MODE_PRIVATE);
        installCrashRecorder();
        showOpening();

        String lastCrash = prefs.getString("lastCrash", null);
        if (lastCrash != null) {
            prefs.edit().remove("lastCrash").apply();
            showProblem("The app closed unexpectedly last time.", lastCrash);
            return;
        }
        try {
            Notifs.createChannels(this);
            Scheduler.scheduleAll(this);
        } catch (Throwable t) {
            Log.e(TAG, "setup failed", t);
            toast("Reminders couldn't be set up: " + t.getMessage());
        }
    }

    /** Each time we're back in front: continue setup, or open the tracker. */
    @Override
    protected void onResume() {
        super.onResume();
        if (showingProblem || launched) return;
        try { nextStep(); }
        catch (Throwable t) { showProblem("Builder Day couldn't start.", trace(t)); }
    }

    private void nextStep() {
        // 1. Notifications (Android 13+)
        if (Build.VERSION.SDK_INT >= 33 && !notifAsked
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            notifAsked = true;
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, RC_NOTIF);
            return;   // onResume runs again when the dialog closes
        }
        // 2. Exact alarms (Android 12 asks; 13+ grants it through USE_EXACT_ALARM)
        AlarmManager am = getSystemService(AlarmManager.class);
        if (!Scheduler.canExact(am) && !prefs.getBoolean("askedExact", false)) {
            prefs.edit().putBoolean("askedExact", true).apply();
            if (tryOpen(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:" + getPackageName())))) {
                toast("Allow Builder Day to set alarms, then come back.");
                return;
            }
        }
        // 3. Full-screen wake-up screen (Android 14+ on some phones)
        NotificationManager nm = getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 34 && !nm.canUseFullScreenIntent() && !prefs.getBoolean("askedFullScreen", false)) {
            prefs.edit().putBoolean("askedFullScreen", true).apply();
            if (tryOpen(new Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT, Uri.parse("package:" + getPackageName())))) {
                toast("Turn this on so the 05:00 alarm can show the Wake up screen, then come back.");
                return;
            }
        }
        // Permissions may have changed; make sure alarms are set with them
        try { Scheduler.scheduleAll(this); } catch (Throwable t) { Log.w(TAG, "reschedule failed", t); }
        // 4. The tracker
        openTracker();
    }

    @Override
    public void onRequestPermissionsResult(int rc, String[] perms, int[] results) {
        // onResume follows and continues setup
    }

    private void openTracker() {
        launched = true;
        try {
            Uri site = Uri.parse(getString(R.string.site_url));
            TrustedWebActivityIntentBuilder builder = new TrustedWebActivityIntentBuilder(site)
                    .setDefaultColorSchemeParams(new CustomTabColorSchemeParams.Builder()
                            .setToolbarColor(0xFF123A26)
                            .setNavigationBarColor(0xFF0D1611)
                            .build());
            launcher = new TwaLauncher(this);
            launcher.launch(builder, null, null, null, TwaLauncher.CCT_FALLBACK_STRATEGY);
        } catch (Throwable t) {
            Log.e(TAG, "trusted web activity failed", t);
            openInBrowser();
            finish();
        }
    }

    /** Back from the tracker means the person is leaving the app. */
    @Override
    protected void onRestart() {
        super.onRestart();
        if (launched) finish();
    }

    @Override
    protected void onDestroy() {
        if (launcher != null) launcher.destroy();
        super.onDestroy();
    }

    private void openInBrowser() {
        Uri site = Uri.parse(getString(R.string.site_url));
        Intent chrome = new Intent(Intent.ACTION_VIEW, site).setPackage("com.android.chrome").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        if (!tryOpen(chrome)) tryOpen(new Intent(Intent.ACTION_VIEW, site).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
    }

    /** Some phones (MIUI/HyperOS among them) leave out standard settings screens; never crash over one. */
    private boolean tryOpen(Intent i) {
        try { startActivity(i); return true; }
        catch (Throwable t) { Log.w(TAG, "couldn't open " + i.getAction(), t); return false; }
    }

    private void showOpening() {
        TextView t = new TextView(this);
        t.setText("Opening Builder Day…");
        t.setTextSize(18);
        t.setTextColor(0xFFE4ECE6);
        t.setGravity(Gravity.CENTER);
        t.setBackgroundColor(0xFF0D1611);
        setContentView(t);
    }

    private void showProblem(String headline, String detail) {
        showingProblem = true;
        String report = headline + "\n\nPhone: " + Build.MANUFACTURER + " " + Build.MODEL + ", Android " + Build.VERSION.RELEASE
                + " (API " + Build.VERSION.SDK_INT + ")\nApp: " + BuildConfigInfo.VERSION + "\n\n" + detail;
        new AlertDialog.Builder(this, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                .setTitle("Something went wrong")
                .setMessage(report)
                .setCancelable(false)
                .setPositiveButton("Open in Chrome", (d, w) -> { openInBrowser(); finish(); })
                .setNeutralButton("Copy details", (d, w) -> {
                    ClipboardManager cm = getSystemService(ClipboardManager.class);
                    cm.setPrimaryClip(ClipData.newPlainText("Builder Day error", report));
                    toast("Copied. Paste it to Claude.");
                    finish();
                })
                .setNegativeButton("Try again", (d, w) -> { showingProblem = false; recreate(); })
                .show();
    }

    private void installCrashRecorder() {
        Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, t) -> {
            getSharedPreferences("setup", MODE_PRIVATE).edit().putString("lastCrash", trace(t)).commit();
            if (previous != null) previous.uncaughtException(thread, t);
        });
    }

    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }

    static String trace(Throwable t) {
        StringWriter sw = new StringWriter();
        t.printStackTrace(new PrintWriter(sw));
        String s = sw.toString();
        return s.length() > 2500 ? s.substring(0, 2500) + "…" : s;
    }
}
