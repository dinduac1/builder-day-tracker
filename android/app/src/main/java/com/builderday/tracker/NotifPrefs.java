package com.builderday.tracker;

import android.content.Context;
import android.content.SharedPreferences;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.media.RingtoneManager;
import android.net.Uri;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * What the person chose in ORDO → Settings → Notifications: a master switch, each block on/off with its own sound,
 * and the extras (5-minute warnings, nag, crew alerts, wake alarm). Everything is on by default.
 */
final class NotifPrefs {
    /** Sounds people can pick, in the order shown. "default" = the phone's notification sound, "silent" = none. */
    static final String[][] SOUNDS = {
        {"s_message", "Message (ORDO)"}, {"s_train", "Punch"}, {"s_build", "Rising marimba"}, {"s_publish", "Bright arpeggio"}, {"s_connect", "Ping"},
        {"s_review", "Closing bells"}, {"s_study", "Clear bell"}, {"s_lunch", "Warm chime"}, {"s_break", "Easy pluck"},
        {"s_exec", "Knock-knock"}, {"s_drills", "Drill beeps"}, {"s_life", "Warm chord"}, {"s_wind", "Soft swell"},
        {"s_sleep", "Low hush"}, {"s_warn", "Tick-tick"}, {"s_nag", "Urgent"}, {"default", "Phone default"}, {"silent", "Silent"},
    };
    static final String[] EXTRAS = {"warn", "nag", "crew", "wake", "chat"};
    private static MediaPlayer preview;

    private static SharedPreferences p(Context ctx) { return ctx.getSharedPreferences("notif", Context.MODE_PRIVATE); }

    static boolean master(Context ctx) { return p(ctx).getBoolean("all", true); }
    static boolean extra(Context ctx, String key) { return master(ctx) && p(ctx).getBoolean("x_" + key, true); }
    static boolean blockOn(Context ctx, String blockId) { return master(ctx) && p(ctx).getBoolean("on_" + blockId, true); }

    static boolean validSound(String s) { for (String[] x : SOUNDS) if (x[0].equals(s)) return true; return false; }

    /** The sound for a block: the person's pick, else the block's own sound, else the shared one. */
    static String soundOf(Context ctx, String key) {
        String s = p(ctx).getString("snd_" + key, null);
        if (s != null && validSound(s)) return s;
        if ("warn".equals(key)) return "s_warn";
        if ("crew".equals(key)) return "s_connect";
        if ("chat".equals(key)) return "s_message";
        return Notifs.hasSound(ctx, key) ? "s_" + key : "s_exec";
    }

    static Uri uri(Context ctx, String sound) {
        if ("silent".equals(sound)) return null;
        if ("default".equals(sound)) return RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
        return Notifs.sound(ctx, sound);
    }

    static void set(Context ctx, String key, boolean on) {
        SharedPreferences.Editor e = p(ctx).edit();
        if ("all".equals(key)) e.putBoolean("all", on);
        else if (key.startsWith("block:")) e.putBoolean("on_" + key.substring(6), on);
        else e.putBoolean("x_" + key, on);
        e.apply();
    }

    static void setSound(Context ctx, String key, String sound) {
        if (!validSound(sound)) return;
        p(ctx).edit().putString("snd_" + key, sound).apply();
    }

    static String json(Context ctx) {
        try {
            JSONObject o = new JSONObject();
            o.put("all", master(ctx));
            JSONObject ex = new JSONObject();
            for (String k : EXTRAS) ex.put(k, p(ctx).getBoolean("x_" + k, true));
            o.put("extras", ex);
            o.put("warnSound", soundOf(ctx, "warn"));
            o.put("crewSound", soundOf(ctx, "crew"));
            o.put("chatSound", soundOf(ctx, "chat"));
            JSONObject bl = new JSONObject();
            for (Schedule.Block b : Schedule.BLOCKS) {
                JSONObject x = new JSONObject();
                x.put("on", p(ctx).getBoolean("on_" + b.id, true));
                x.put("sound", soundOf(ctx, b.id));
                bl.put(b.id, x);
            }
            o.put("blocks", bl);
            JSONArray snd = new JSONArray();
            for (String[] s : SOUNDS) snd.put(new JSONObject().put("id", s[0]).put("label", s[1]));
            o.put("sounds", snd);
            return o.toString();
        } catch (Exception e) { return "{}"; }
    }

    /** Play a sound once so people can hear it before choosing. */
    static void preview(Context ctx, String sound) {
        try {
            if (preview != null) { preview.release(); preview = null; }
            Uri u = uri(ctx, sound);
            if (u == null) return;
            preview = new MediaPlayer();
            preview.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_EVENT)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
            preview.setDataSource(ctx, u);
            preview.setOnCompletionListener(mp -> { mp.release(); if (preview == mp) preview = null; });
            preview.prepare();
            preview.start();
        } catch (Exception ignored) { }
    }

    private NotifPrefs() {}
}
