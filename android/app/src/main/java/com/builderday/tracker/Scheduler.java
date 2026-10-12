package com.builderday.tracker;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

/**
 * Keeps two alarms pending at all times:
 *  - the next block reminder (start or 5-minute warning), exact, allowed while the phone is idle;
 *  - the next 05:00 wake-up, as a real alarm clock (shows in the status bar, bypasses Do Not Disturb).
 * Each alarm, when it fires, schedules the one after it.
 */
final class Scheduler {
    static final String EXTRA_KIND = "kind", EXTRA_BLOCK = "block", EXTRA_AT = "at";
    static final String KIND_WAKE = "wake";
    private static final int RC_NEXT = 1, RC_WAKE = 2;

    static void scheduleAll(Context ctx) {
        scheduleNextReminder(ctx);
        scheduleWake(ctx, Schedule.nextAt(System.currentTimeMillis(), Schedule.byId("wake").startMin()));
    }

    static void scheduleNextReminder(Context ctx) {
        long now = System.currentTimeMillis(), best = Long.MAX_VALUE;
        Schedule.Event next = null;
        for (Schedule.Event e : Schedule.dailyEvents()) {
            long t = Schedule.nextAt(now, e.minute);
            if (t < best) { best = t; next = e; }
        }
        if (next == null) return;
        Intent i = new Intent(ctx, AlarmReceiver.class)
                .putExtra(EXTRA_KIND, next.kind == Schedule.Event.START ? "start" : "ending")
                .putExtra(EXTRA_BLOCK, next.block.id)
                .putExtra(EXTRA_AT, best);
        PendingIntent pi = PendingIntent.getBroadcast(ctx, RC_NEXT, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager am = ctx.getSystemService(AlarmManager.class);
        if (canExact(am)) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, best, pi);
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, best, pi);
    }

    static void scheduleWake(Context ctx, long at) {
        Intent i = new Intent(ctx, AlarmReceiver.class).putExtra(EXTRA_KIND, KIND_WAKE).putExtra(EXTRA_AT, at);
        PendingIntent fire = PendingIntent.getBroadcast(ctx, RC_WAKE, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent show = PendingIntent.getActivity(ctx, RC_WAKE, new Intent(ctx, StartActivity.class), PendingIntent.FLAG_IMMUTABLE);
        AlarmManager am = ctx.getSystemService(AlarmManager.class);
        if (canExact(am)) am.setAlarmClock(new AlarmManager.AlarmClockInfo(at, show), fire);
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, fire);
    }

    static boolean canExact(AlarmManager am) {
        return Build.VERSION.SDK_INT < 31 || am.canScheduleExactAlarms();
    }

    private Scheduler() {}
}
