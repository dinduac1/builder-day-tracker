package com.builderday.tracker;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.net.Uri;

/**
 * One notification channel per block, each with its own sound (res/raw/s_<block>.wav), plus one for
 * "5 minutes left" warnings. Android fixes a channel's sound when it's created, so changing a sound means
 * bumping CH_VERSION. People can still mute or change any channel in the phone's notification settings.
 */
final class Notifs {
    static final String CH_VERSION = "v1";
    static final String CH_WARN = "warn_" + CH_VERSION, CH_WAKE = "wake_" + CH_VERSION, CH_NAG = "nag_" + CH_VERSION;

    static String channelFor(String blockId) { return "block_" + blockId + "_" + CH_VERSION; }

    static void createChannels(Context ctx) {
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        AudioAttributes notif = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
        for (Schedule.Block b : Schedule.BLOCKS) {
            if (b.id.equals("wake")) continue;
            NotificationChannel ch = new NotificationChannel(channelFor(b.id), b.name.split(" — ")[0], NotificationManager.IMPORTANCE_HIGH);
            ch.setDescription("Starts at " + b.start);
            ch.setSound(sound(ctx, "s_" + b.id), notif);
            ch.enableVibration(true);
            nm.createNotificationChannel(ch);
        }
        NotificationChannel warn = new NotificationChannel(CH_WARN, "5 minutes left", NotificationManager.IMPORTANCE_HIGH);
        warn.setDescription("Heads-up before each block ends");
        warn.setSound(sound(ctx, "s_warn"), notif);
        nm.createNotificationChannel(warn);

        NotificationChannel nag = new NotificationChannel(CH_NAG, "Nag: haven't started", NotificationManager.IMPORTANCE_HIGH);
        nag.setDescription("Repeats every 10 minutes until you start a Daily Five block");
        nag.setSound(sound(ctx, "s_nag"), new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_RINGTONE)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
        nag.enableVibration(true);
        nag.setVibrationPattern(new long[]{0, 400, 150, 400, 150, 400});
        nm.createNotificationChannel(nag);

        // The wake-up alarm plays its own looping sound (WakeService), so this channel is silent.
        NotificationChannel wake = new NotificationChannel(CH_WAKE, "Wake-up alarm", NotificationManager.IMPORTANCE_HIGH);
        wake.setDescription("05:00 alarm. Rings until you tap I'm up.");
        wake.setSound(null, null);
        wake.setBypassDnd(true);
        nm.createNotificationChannel(wake);
    }

    static Uri sound(Context ctx, String raw) {
        return Uri.parse("android.resource://" + ctx.getPackageName() + "/raw/" + raw);
    }

    static PendingIntent openTracker(Context ctx, int rc) {
        Intent i = new Intent(ctx, StartActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        return PendingIntent.getActivity(ctx, rc, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** A Daily Five block's reminder, with a "Starting now" button that stops the nag. */
    static void postWithStart(Context ctx, int id, String channel, String title, String text, String blockId) {
        ctx.getSystemService(NotificationManager.class).notify(id, builder(ctx, id, channel, title, text)
                .addAction(new Notification.Action.Builder(null, "Starting now", Nag.startingNow(ctx, blockId)).build())
                .build());
    }

    static void postNag(Context ctx, Schedule.Block b, String title, String text) {
        int id = 3000 + Schedule.indexOf(b.id);
        ctx.getSystemService(NotificationManager.class).notify(id, builder(ctx, id, CH_NAG, title, text)
                .setCategory(Notification.CATEGORY_ALARM)
                .addAction(new Notification.Action.Builder(null, "Starting now", Nag.startingNow(ctx, b.id)).build())
                .build());
    }

    private static Notification.Builder builder(Context ctx, int id, String channel, String title, String text) {
        return new Notification.Builder(ctx, channel)
                .setSmallIcon(R.drawable.ic_stat)
                .setColor(0xFF1F6B43)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setCategory(Notification.CATEGORY_REMINDER)
                .setContentIntent(openTracker(ctx, id))
                .setAutoCancel(true);
    }

    static void post(Context ctx, int id, String channel, String title, String text) {
        Notification n = new Notification.Builder(ctx, channel)
                .setSmallIcon(R.drawable.ic_stat)
                .setColor(0xFF1F6B43)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setCategory(Notification.CATEGORY_REMINDER)
                .setContentIntent(openTracker(ctx, id))
                .setAutoCancel(true)
                .build();
        ctx.getSystemService(NotificationManager.class).notify(id, n);
    }

    private Notifs() {}
}
