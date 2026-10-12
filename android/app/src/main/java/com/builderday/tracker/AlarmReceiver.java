package com.builderday.tracker;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Fires for every scheduled moment: shows the reminder (or starts the wake alarm), then schedules the next one. */
public class AlarmReceiver extends BroadcastReceiver {
    private static final long STALE_MS = 10 * 60 * 1000L;   // skip reminders delivered more than 10 min late

    @Override
    public void onReceive(Context ctx, Intent intent) {
        String kind = intent.getStringExtra(Scheduler.EXTRA_KIND);
        long at = intent.getLongExtra(Scheduler.EXTRA_AT, System.currentTimeMillis());
        boolean fresh = System.currentTimeMillis() - at < STALE_MS;
        Notifs.createChannels(ctx);

        if (Scheduler.KIND_WAKE.equals(kind)) {
            if (fresh) ctx.startForegroundService(new Intent(ctx, WakeService.class));
            Scheduler.scheduleWake(ctx, Schedule.nextAt(System.currentTimeMillis(), Schedule.byId("wake").startMin()));
            return;
        }

        Schedule.Block b = Schedule.byId(intent.getStringExtra(Scheduler.EXTRA_BLOCK));
        if (fresh) {
            if ("ending".equals(kind)) {
                Notifs.post(ctx, 2000 + index(b), Notifs.CH_WARN,
                        Schedule.WARN_MINUTES + " min left: " + b.name,
                        "Ends at " + b.end + ". Log it in the tracker before you move on.");
            } else if (b.id.equals("train") && Schedule.isSunday(at)) {
                Notifs.post(ctx, 1000 + index(b), Notifs.channelFor(b.id), "Rest day · " + b.start,
                        "Mobility and a walk. Recover for Monday.");
            } else {
                Notifs.post(ctx, 1000 + index(b), Notifs.channelFor(b.id), b.name + " · " + b.start, b.desc);
            }
        }
        Scheduler.scheduleNextReminder(ctx);
    }

    private static int index(Schedule.Block b) {
        for (int i = 0; i < Schedule.BLOCKS.length; i++) if (Schedule.BLOCKS[i] == b) return i;
        return 0;
    }
}
