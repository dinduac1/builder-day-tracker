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
import android.widget.Toast;

import com.google.androidbrowserhelper.trusted.LauncherActivity;

import java.io.PrintWriter;
import java.io.StringWriter;

/**
 * App entry point. Asks once for the permissions reminders need (notifications, exact alarms, full-screen
 * wake-up), makes sure every alarm is scheduled, then opens the tracker.
 * Nothing here is allowed to crash the app: any failure is shown on screen with a way to keep going,
 * and a crash anywhere else in the app is saved and shown on the next launch.
 */
public class StartActivity extends Activity {
    private static final int RC_NOTIF = 10;
    private static final String TAG = "BuilderDay";
    private SharedPreferences prefs;

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
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, RC_NOTIF);
                return;
            }
            proceed();
        } catch (Throwable t) {
            showProblem("Builder Day couldn't start.", trace(t));
        }
    }

    @Override
    public void onRequestPermissionsResult(int rc, String[] perms, int[] results) {
        try { proceed(); } catch (Throwable t) { showProblem("Builder Day couldn't start.", trace(t)); }
    }

    private void proceed() {
        try { Scheduler.scheduleAll(this); }
        catch (Throwable t) { Log.e(TAG, "scheduling failed", t); toast("Reminders couldn't be scheduled: " + t.getMessage()); }

        // Open the tracker first so any one-time settings screen below sits on top and Back returns to it
        openTracker();

        // Android 12: exact alarms need the person's OK (13+ grants it through USE_EXACT_ALARM)
        try {
            AlarmManager am = getSystemService(AlarmManager.class);
            if (!Scheduler.canExact(am) && !prefs.getBoolean("askedExact", false)) {
                prefs.edit().putBoolean("askedExact", true).apply();
                tryOpen(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:" + getPackageName())));
            }
        } catch (Throwable t) { Log.w(TAG, "exact alarm check failed", t); }

        // Android 14: the full-screen wake-up screen needs the person's OK on some phones
        try {
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (Build.VERSION.SDK_INT >= 34 && !nm.canUseFullScreenIntent() && !prefs.getBoolean("askedFullScreen", false)) {
                prefs.edit().putBoolean("askedFullScreen", true).apply();
                tryOpen(new Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT, Uri.parse("package:" + getPackageName())));
            }
        } catch (Throwable t) { Log.w(TAG, "full-screen check failed", t); }
        finish();
    }

    /** Full-screen tracker via Chrome; if that can't start, the plain browser. */
    private void openTracker() {
        try {
            startActivity(new Intent(this, LauncherActivity.class));
        } catch (Throwable t) {
            Log.e(TAG, "trusted web activity failed", t);
            openInBrowser();
        }
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

    private void showProblem(String headline, String detail) {
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
                .setNegativeButton("Try again", (d, w) -> { recreate(); })
                .show();
    }

    private void installCrashRecorder() {
        Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread, t) -> {
            getSharedPreferences("setup", MODE_PRIVATE).edit().putString("lastCrash", trace(t)).commit();
            if (previous != null) previous.uncaughtException(thread, t);
        });
    }

    /** A visible "Opening…" screen, so it's clear the app is working while the tracker loads. */
    private void showOpening() {
        android.widget.TextView t = new android.widget.TextView(this);
        t.setText("Opening Builder Day…");
        t.setTextSize(18);
        t.setTextColor(0xFFE4ECE6);
        t.setGravity(android.view.Gravity.CENTER);
        t.setBackgroundColor(0xFF0D1611);
        setContentView(t);
    }

    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }

    static String trace(Throwable t) {
        StringWriter sw = new StringWriter();
        t.printStackTrace(new PrintWriter(sw));
        String s = sw.toString();
        return s.length() > 2500 ? s.substring(0, 2500) + "…" : s;
    }
}
