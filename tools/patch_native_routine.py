"""One-off: Android follows the person's own routine (sent from the web app) and moves to com.ordo.app."""
import os
J = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "android", "app", "src", "main", "java", "com", "builderday", "tracker")
os.chdir(J)

def edit(p, pairs):
    s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (p, a[:70])
        s = s.replace(a, b, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s)

edit("Schedule.java", [
    ("import java.util.ArrayList;", "import android.content.Context;\n\nimport org.json.JSONArray;\nimport org.json.JSONObject;\n\nimport java.util.ArrayList;"),
    ("/** The Full-Time Builder Day. Keep in step with BLOCKS in index.html and worker.js. */",
     "/** The person's timed routine. Defaults to the Full-Time Builder Day; the web app sends its own via setRoutine. */"),
    ("""        final String id, start, end, name, desc;
        Block(String id, String start, String end, String name, String desc) {
            this.id = id; this.start = start; this.end = end; this.name = name; this.desc = desc;
        }""", """        final String id, start, end, name, desc;
        final boolean five;
        Block(String id, String start, String end, String name, String desc) { this(id, start, end, name, desc, Nag.DEFAULT_FIVE.contains(id)); }
        Block(String id, String start, String end, String name, String desc, boolean five) {
            this.id = id; this.start = start; this.end = end; this.name = name; this.desc = desc; this.five = five;
        }"""),
    ("static final Block[] BLOCKS = {", "static final Block[] DEFAULTS = {"),
    ("    static final int WARN_MINUTES = 5;", """    static volatile Block[] BLOCKS = DEFAULTS;

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
                if (!s.matches("\\\\d\\\\d:\\\\d\\\\d") || !e.matches("\\\\d\\\\d:\\\\d\\\\d")) continue;
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

    static final int WARN_MINUTES = 5;"""),
    ("""            if (!b.id.equals("wake")) out.add""", """            if (b.startMin() == b.endMin()) continue;
            if (!b.id.equals("wake")) out.add"""),
    ("""        for (Block b : BLOCKS) if (b.id.equals(id)) return b;
        return BLOCKS[0];""", """        Block b = find(id);
        return b != null ? b : BLOCKS[0];"""),
])

edit("Nag.java", [
    ('    static final String[] FIVE = {"train", "build", "publish", "connect", "review"};',
     '    static final java.util.List<String> DEFAULT_FIVE = java.util.Arrays.asList("train", "build", "publish", "connect", "review");'),
    ("""        for (String f : FIVE) if (f.equals(id)) return true;
        return false;""", """        Schedule.Block b = Schedule.find(id);
        return b != null && b.five;"""),
])

edit("Notifs.java", [
    ('    static String channelFor(String blockId) { return "block_" + blockId + "_" + CH_VERSION; }',
     '''    static final String CH_OTHER = "block_other_" + CH_VERSION;
    /** Blocks from the original day have their own sound; blocks people create share one channel. */
    static boolean hasSound(Context ctx, String blockId) {
        return ctx.getResources().getIdentifier("s_" + blockId, "raw", ctx.getPackageName()) != 0;
    }
    static String channelFor(Context ctx, String blockId) { return hasSound(ctx, blockId) ? "block_" + blockId + "_" + CH_VERSION : CH_OTHER; }'''),
    ("""        for (Schedule.Block b : Schedule.BLOCKS) {
            if (b.id.equals("wake")) continue;""", """        NotificationChannel other = new NotificationChannel(CH_OTHER, "Your routine blocks", NotificationManager.IMPORTANCE_HIGH);
        other.setDescription("Blocks you added to your routine");
        other.setSound(sound(ctx, "s_exec"), notif);
        other.enableVibration(true);
        nm.createNotificationChannel(other);
        for (Schedule.Block b : Schedule.BLOCKS) {
            if (b.id.equals("wake") || !hasSound(ctx, b.id)) continue;"""),
])

s = open("AlarmReceiver.java", encoding="utf-8").read()
s = s.replace("Notifs.channelFor(b.id)", "Notifs.channelFor(ctx, b.id)")
open("AlarmReceiver.java", "w", encoding="utf-8", newline="\n").write(s)
edit("AlarmReceiver.java", [
    ("""        if (Scheduler.KIND_WAKE.equals(kind)) {
            if (fresh)""", """        if (Scheduler.KIND_WAKE.equals(kind)) {
            if (Schedule.find("wake") == null) return;   // the routine has no wake-up any more
            if (fresh)"""),
    ("""        Schedule.Block b = Schedule.byId(intent.getStringExtra(Scheduler.EXTRA_BLOCK));
""", """        Schedule.Block b = Schedule.find(intent.getStringExtra(Scheduler.EXTRA_BLOCK));
        if (b == null) { Scheduler.scheduleNextReminder(ctx); return; }   // block was removed from the routine
"""),
])

edit("Scheduler.java", [
    ("""        scheduleNextReminder(ctx);
        scheduleWake(ctx, Schedule.nextAt(System.currentTimeMillis(), Schedule.byId("wake").startMin()));
    }""", """        scheduleNextReminder(ctx);
        Schedule.Block w = Schedule.find("wake");
        if (w != null) scheduleWake(ctx, Schedule.nextAt(System.currentTimeMillis(), w.startMin()));
        else ctx.getSystemService(AlarmManager.class).cancel(PendingIntent.getBroadcast(ctx, RC_WAKE, new Intent(ctx, AlarmReceiver.class), PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));
    }"""),
])

t = open("TrackerActivity.java", encoding="utf-8").read()
pairs = [("        @JavascriptInterface public void setScheduleEnabled(boolean on) { Scheduler.setEnabled(getApplicationContext(), on); }",
          """        @JavascriptInterface public void setScheduleEnabled(boolean on) { Scheduler.setEnabled(getApplicationContext(), on); }
        @JavascriptInterface public void setRoutine(String json) {
            android.content.Context c = getApplicationContext();
            Schedule.save(c, json);
            Notifs.createChannels(c);
            Scheduler.scheduleAll(c);
        }""")]
edit("TrackerActivity.java", pairs)

open("App.java", "w", encoding="utf-8", newline="\n").write('''package com.builderday.tracker;

import android.app.Application;

/** Loads the saved routine before any alarm, service or screen runs. */
public class App extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        Schedule.load(this);
    }
}
''')
edit(os.path.join("..", "..", "..", "..", "AndroidManifest.xml"), [("<application\n", '<application\n        android:name=".App"\n')])
edit(os.path.join("..", "..", "..", "..", "..", "..", "build.gradle"), [("applicationId 'com.builderday.tracker'", "applicationId 'com.ordo.app'")])
print("ok")
