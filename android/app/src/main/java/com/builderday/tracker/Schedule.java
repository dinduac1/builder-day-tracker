package com.builderday.tracker;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;

/** The person's timed routine. Defaults to the Full-Time Builder Day; the web app sends its own via setRoutine. */
final class Schedule {
    static final class Block {
        final String id, start, end, name, desc;
        final boolean five;
        Block(String id, String start, String end, String name, String desc) { this(id, start, end, name, desc, Nag.DEFAULT_FIVE.contains(id)); }
        Block(String id, String start, String end, String name, String desc, boolean five) {
            this.id = id; this.start = start; this.end = end; this.name = name; this.desc = desc; this.five = five;
        }
        int startMin() { return toMin(start); }
        int endMin() { return toMin(end); }
    }

    static final Block[] DEFAULTS = {
        new Block("wake",    "05:00", "05:30", "Wake", "Water, light, no phone. Read tonight's plan from last night."),
        new Block("train",   "05:30", "06:45", "TRAIN", "Full body + core. Log your reps."),
        new Block("study",   "06:45", "07:15", "Study", "30 min reading in the craft."),
        new Block("build",   "07:15", "09:15", "BUILD — Deep Work 1", "The money-making work. Phone in another room."),
        new Block("break",   "09:15", "09:45", "Break", "Food. Walk. No feeds."),
        new Block("publish", "09:45", "11:15", "PUBLISH — Deep Work 2", "Create + ship today's content."),
        new Block("connect", "11:15", "12:00", "CONNECT", "10 outreach touches. Follow-ups first."),
        new Block("lunch",   "12:00", "13:00", "Lunch + admin", "Emails, invoices, small tasks — never in deep work."),
        new Block("exec",    "13:00", "16:00", "Execution block", "Client work, sales calls, systems, editing."),
        new Block("drills",  "16:00", "17:00", "Learning/skill drills", "Deliberate practice on your weakest skill."),
        new Block("life",    "17:00", "20:00", "Life", "People, food, family, faith, community."),
        new Block("review",  "20:30", "20:45", "REVIEW", "Did I do the Five? Write tomorrow's top 3 and one line of gratitude."),
        new Block("wind",    "21:00", "22:00", "Wind down", "No screens after 21:30."),
        new Block("sleep",   "22:00", "05:00", "Sleep", "7+ hours, non-negotiable."),
    };

    static volatile Block[] BLOCKS = DEFAULTS;

    /** Load the routine the web app saved (falls back to the default day). Called from App.onCreate. */
    static void load(Context ctx) {
        String j = ctx.getSharedPreferences("schedule", Context.MODE_PRIVATE).getString("routine", null);
        if (j == null) { BLOCKS = DEFAULTS; return; }
        try {
            JSONArray a = new JSONArray(j);
            List<Block> l = new ArrayList<>();
            for (int i = 0; i < a.length(); i++) {
                JSONObject o = a.getJSONObject(i);
                String s = o.getString("s"), e = o.getString("e");
                if (!s.matches("\\d\\d:\\d\\d") || !e.matches("\\d\\d:\\d\\d")) continue;
                l.add(new Block(o.getString("id"), s, e, o.optString("name", ""), o.optString("desc", ""), o.optBoolean("five", false)));
            }
            BLOCKS = l.isEmpty() ? DEFAULTS : l.toArray(new Block[0]);
        } catch (Exception ex) { BLOCKS = DEFAULTS; }
    }

    static void save(Context ctx, String json) {
        ctx.getSharedPreferences("schedule", Context.MODE_PRIVATE).edit().putString("routine", json).apply();
        load(ctx);
    }

    /** The block with this id, or null if the routine no longer has it. */
    static Block find(String id) {
        if (id == null) return null;
        for (Block b : BLOCKS) if (b.id.equals(id)) return b;
        return null;
    }

    static final int WARN_MINUTES = 5;

    /** One thing that happens at a time of day. */
    static final class Event {
        static final int START = 0, ENDING = 1;
        final int minute, kind; final Block block;
        Event(int minute, int kind, Block block) { this.minute = minute; this.kind = kind; this.block = block; }
    }

    /** Block starts (Wake is the alarm, handled separately) and 5-minute warnings before each block ends. */
    static List<Event> dailyEvents() {
        List<Event> out = new ArrayList<>();
        for (Block b : BLOCKS) {
            if (b.startMin() == b.endMin()) continue;
            if (!b.id.equals("wake")) out.add(new Event(b.startMin(), Event.START, b));
            if (!b.id.equals("sleep")) out.add(new Event(b.endMin() - WARN_MINUTES, Event.ENDING, b));
        }
        return out;
    }

    static Block byId(String id) {
        Block b = find(id);
        return b != null ? b : BLOCKS[0];
    }

    static int indexOf(String id) {
        for (int i = 0; i < BLOCKS.length; i++) if (BLOCKS[i].id.equals(id)) return i;
        return 0;
    }

    static int toMin(String hm) {
        return Integer.parseInt(hm.substring(0, 2)) * 60 + Integer.parseInt(hm.substring(3, 5));
    }

    /** Next time (epoch ms) strictly after `now` that falls at `minuteOfDay` local time. */
    static long nextAt(long now, int minuteOfDay) {
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(now);
        c.set(Calendar.HOUR_OF_DAY, minuteOfDay / 60);
        c.set(Calendar.MINUTE, minuteOfDay % 60);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
        if (c.getTimeInMillis() <= now) c.add(Calendar.DAY_OF_YEAR, 1);
        return c.getTimeInMillis();
    }

    static boolean isSunday(long when) {
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(when);
        return c.get(Calendar.DAY_OF_WEEK) == Calendar.SUNDAY;
    }

    private Schedule() {}
}
