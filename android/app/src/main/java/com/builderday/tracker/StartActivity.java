package com.builderday.tracker;

import android.Manifest;
import android.app.Activity;
import android.app.AlarmManager;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;

import com.google.androidbrowserhelper.trusted.LauncherActivity;

/**
 * App entry point. Asks once for the permissions reminders need (notifications, exact alarms, full-screen
 * wake-up), makes sure every alarm is scheduled, then opens the tracker.
 */
public class StartActivity extends Activity {
    private static final int RC_NOTIF = 10;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        Notifs.createChannels(this);
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, RC_NOTIF);
            return;
        }
        proceed();
    }

    @Override
    public void onRequestPermissionsResult(int rc, String[] perms, int[] results) {
        proceed();
    }

    private void proceed() {
        Scheduler.scheduleAll(this);
        SharedPreferences prefs = getSharedPreferences("setup", MODE_PRIVATE);
        // Open the tracker first so any one-time settings screen below sits on top and Back returns to it
        startActivity(new Intent(this, LauncherActivity.class));

        // Android 12: exact alarms need the person's OK (13+ grants it through USE_EXACT_ALARM)
        AlarmManager am = getSystemService(AlarmManager.class);
        if (!Scheduler.canExact(am) && !prefs.getBoolean("askedExact", false)) {
            prefs.edit().putBoolean("askedExact", true).apply();
            startActivity(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:" + getPackageName())));
        }
        // Android 14: the full-screen wake-up screen needs the person's OK on some phones
        NotificationManager nm = getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 34 && !nm.canUseFullScreenIntent() && !prefs.getBoolean("askedFullScreen", false)) {
            prefs.edit().putBoolean("askedFullScreen", true).apply();
            startActivity(new Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT, Uri.parse("package:" + getPackageName())));
        }
        finish();
    }
}
