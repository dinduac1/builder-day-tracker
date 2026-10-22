package com.builderday.tracker;

import android.app.AlarmManager;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

/**
 * Nag mode for the Daily Five. When a Five block starts, a follow-up is booked for 10 minutes later.
 * Unless the block has been started (tapping "Starting now", or ticking / timing / logging it in the tracker),
 * each follow-up re-notifies with an urgent sound, up to MAX_NAGS times, and never after the block ends.
 */
final class Nag {
    static final String[] FIVE = {"train", "build", "publish", "connect", "review"};
    static final int EVERY_MIN = 10, MAX_NAGS = 3;
    static final String KIND_NAG = "nag", KIND_ACK = "ack", EXTRA_COUNT = "count";
    private static final int RC_NAG = 3;

    static boolean isFive(String id) {
        for (String f : FIVE) if (f.equals(id)) return true;
        return false;
    }

    private static String today() { return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date()); }

    private static String key(String blockId) { return "started_" + today() + "_" + blockId; }

    static boolean started(Context ctx, String blockId) {
        return ctx.getSharedPreferences("nag", Context.MODE_PRIVATE).getBoolean(key(blockId), false);
    }

    /** The block has begun: stop nagging and clear its notifications. */
    static void markStarted(Context ctx, String blockId) {
        ctx.getSharedPreferences("nag", Context.MODE_PRIVATE).edit().putBoolean(key(blockId), true).apply();
        int idx = Schedule.indexOf(blockId);
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        nm.cancel(1000 + idx);
        nm.cancel(3000 + idx);
        ctx.getSystemService(AlarmManager.class).cancel(pending(ctx, blockId, 0, 0));
    }

    /** Book follow-up number `count` for this block. */
    static void schedule(Context ctx, String blockId, int count, long at) {
        PendingIntent pi = pending(ctx, blockId, count, at);
        AlarmManager am = ctx.getSystemService(AlarmManager.class);
        if (Scheduler.canExact(am)) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, pi);
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, pi);
    }

    private static PendingIntent pending(Context ctx, String blockId, int count, long at) {
        Intent i = new Intent(ctx, AlarmReceiver.class)
                .putExtra(Scheduler.EXTRA_KIND, KIND_NAG)
                .putExtra(Scheduler.EXTRA_BLOCK, blockId)
                .putExtra(EXTRA_COUNT, count)
                .putExtra(Scheduler.EXTRA_AT, at);
        return PendingIntent.getBroadcast(ctx, RC_NAG, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** "Starting now" button on a block's notifications. */
    static PendingIntent startingNow(Context ctx, String blockId) {
        Intent i = new Intent(ctx, AlarmReceiver.class).putExtra(Scheduler.EXTRA_KIND, KIND_ACK).putExtra(Scheduler.EXTRA_BLOCK, blockId);
        return PendingIntent.getBroadcast(ctx, 4000 + Schedule.indexOf(blockId), i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** Minutes since midnight now, to compare with block times. */
    static int nowMin() {
        Calendar c = Calendar.getInstance();
        return c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE);
    }

    private Nag() {}
}
