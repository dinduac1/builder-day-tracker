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
 * One notification channel per block and per chosen sound (Android fixes a channel's sound when it's created,
 * so a new pick makes a new channel and the old one is deleted). Plus channels for 5-minute warnings, nag,
 * crew alerts and the wake alarm. ORDO → Settings → Notifications drives all of it (NotifPrefs).
 */
final class Notifs {
    static final String CH_VERSION = "v1";
    static final String CH_WAKE = "wake_" + CH_VERSION, CH_NAG = "nag_" + CH_VERSION;
    static final int BRAND = 0xFF7C8BFF;   // ORDO ultramarine: tints the notification icon

    /** Blocks from the original day ship with their own sound. */
    static boolean hasSound(Context ctx, String blockId) {
        return ctx.getResources().getIdentifier("s_" + blockId, "raw", ctx.getPackageName()) != 0;
    }
    static String channelFor(Context ctx, String blockId) { return "blk_" + blockId + "_" + NotifPrefs.soundOf(ctx, blockId); }
    static String warnChannel(Context ctx) { return "warn_" + NotifPrefs.soundOf(ctx, "warn"); }
    static String crewChannel(Context ctx) { return "crew_" + NotifPrefs.soundOf(ctx, "crew"); }
    static String chatChannel(Context ctx) { return "chat_" + NotifPrefs.soundOf(ctx, "chat"); }

    private static void make(NotificationManager nm, Context ctx, String id, String name, String desc, String sound, AudioAttributes aa, java.util.Set<String> keep) {
        NotificationChannel ch = new NotificationChannel(id, name, NotificationManager.IMPORTANCE_HIGH);
        ch.setDescription(desc);
        ch.setSound(NotifPrefs.uri(ctx, sound), aa);
        ch.enableVibration(!"silent".equals(sound));
        nm.createNotificationChannel(ch);
        keep.add(id);
    }

    static void createChannels(Context ctx) {
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        AudioAttributes notif = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
        java.util.Set<String> keep = new java.util.HashSet<>();
        for (Schedule.Block b : Schedule.BLOCKS) {
            if (b.id.equals("wake")) continue;
            make(nm, ctx, channelFor(ctx, b.id), b.name.split(" — ")[0], "Starts at " + b.start, NotifPrefs.soundOf(ctx, b.id), notif, keep);
        }
        make(nm, ctx, warnChannel(ctx), "5 minutes left", "Heads-up before each block ends", NotifPrefs.soundOf(ctx, "warn"), notif, keep);
        make(nm, ctx, crewChannel(ctx), "Crew", "When someone in your crew finishes a goal or a day", NotifPrefs.soundOf(ctx, "crew"), notif, keep);
        make(nm, ctx, chatChannel(ctx), "Crew chat", "New messages, photos and voice notes from your crew", NotifPrefs.soundOf(ctx, "chat"), new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_COMMUNICATION_INSTANT).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build(), keep);
        // channels from older picks (and the first app versions) go, so the phone's settings stay tidy
        for (NotificationChannel c : nm.getNotificationChannels()) {
            String id = c.getId();
            if ((id.startsWith("blk_") || id.startsWith("block_") || id.startsWith("warn_") || id.startsWith("crew_") || id.startsWith("chat_")) && !keep.contains(id))
                nm.deleteNotificationChannel(id);
        }

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

    /** Tapping opens ORDO straight into the crew chat. */
    static PendingIntent openChat(Context ctx, int rc) {
        Intent i = new Intent(ctx, StartActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK).putExtra("open", "chat");
        return PendingIntent.getActivity(ctx, rc, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** A crew chat message: own channel and sound, grouped per crew like a messaging app. */
    static void postChat(Context ctx, String group, String title, String text) {
        if (!NotifPrefs.extra(ctx, "chat")) return;
        createChannels(ctx);
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        int id = Math.abs((title + text + System.currentTimeMillis()).hashCode()) % 100000 + 20000;
        nm.notify(id, new Notification.Builder(ctx, chatChannel(ctx))
                .setSmallIcon(R.drawable.ic_stat).setColor(BRAND)
                .setContentTitle(title).setContentText(text).setStyle(new Notification.BigTextStyle().bigText(text))
                .setCategory(Notification.CATEGORY_MESSAGE).setGroup(group)
                .setContentIntent(openChat(ctx, id)).setAutoCancel(true).build());
        nm.notify(group.hashCode(), new Notification.Builder(ctx, chatChannel(ctx))
                .setSmallIcon(R.drawable.ic_stat).setColor(BRAND).setContentTitle("Crew chat")
                .setGroup(group).setGroupSummary(true).setGroupAlertBehavior(Notification.GROUP_ALERT_CHILDREN)
                .setContentIntent(openChat(ctx, group.hashCode())).setAutoCancel(true).build());
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
                .setColor(BRAND)
                .setContentTitle(title)
                .setContentText(text)
                .setStyle(new Notification.BigTextStyle().bigText(text))
                .setCategory(Notification.CATEGORY_REMINDER)
                .setContentIntent(openTracker(ctx, id))
                .setAutoCancel(true);
    }

    static void postCrew(Context ctx, int id, String title, String text) {
        if (!NotifPrefs.extra(ctx, "crew")) return;
        createChannels(ctx);
        ctx.getSystemService(NotificationManager.class).notify(id, builder(ctx, id, crewChannel(ctx), title, text)
                .setCategory(Notification.CATEGORY_SOCIAL).build());
    }

    static void post(Context ctx, int id, String channel, String title, String text) {
        Notification n = new Notification.Builder(ctx, channel)
                .setSmallIcon(R.drawable.ic_stat)
                .setColor(BRAND)
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
