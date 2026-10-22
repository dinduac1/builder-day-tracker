package com.builderday.tracker;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Fires for every scheduled moment: shows the reminder (or starts the wake alarm, or nags), then schedules the next one. */
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

        if (Nag.KIND_ACK.equals(kind)) {            // "Starting now" tapped
            Nag.markStarted(ctx, b.id);
            return;
        }
        if (Nag.KIND_NAG.equals(kind)) {            // follow-up: still not started?
            int count = intent.getIntExtra(Nag.EXTRA_COUNT, 1);
            int end = b.endMin() > b.startMin() ? b.endMin() : b.endMin() + 1440;
            if (!fresh || Nag.started(ctx, b.id) || Nag.nowMin() >= end) return;
            int late = Nag.nowMin() - b.startMin();
            Notifs.postNag(ctx, b, "You haven't started " + b.name.split(" — ")[0],
                    "It started at " + b.start + " (" + late + " min ago). Get up and begin. Tap Starting now once you have.");
            if (count < Nag.MAX_NAGS) Nag.schedule(ctx, b.id, count + 1, System.currentTimeMillis() + Nag.EVERY_MIN * 60_000L);
            return;
        }

        if (fresh) {
            int idx = Schedule.indexOf(b.id);
            if ("ending".equals(kind)) {
                Notifs.post(ctx, 2000 + idx, Notifs.CH_WARN,
                        Schedule.WARN_MINUTES + " min left: " + b.name,
                        "Ends at " + b.end + ". Log it in the tracker before you move on.");
            } else if (b.id.equals("train") && Schedule.isSunday(at)) {
                Notifs.post(ctx, 1000 + idx, Notifs.channelFor(b.id), "Rest day · " + b.start,
                        "Mobility and a walk. Recover for Monday.");
            } else if (Nag.isFive(b.id)) {
                // a Five block: show it with "Starting now", and book the first follow-up
                Notifs.postWithStart(ctx, 1000 + idx, Notifs.channelFor(b.id), b.name + " · " + b.start, b.desc, b.id);
                if (!Nag.started(ctx, b.id)) Nag.schedule(ctx, b.id, 1, at + Nag.EVERY_MIN * 60_000L);
            } else {
                Notifs.post(ctx, 1000 + idx, Notifs.channelFor(b.id), b.name + " · " + b.start, b.desc);
            }
        }
        Scheduler.scheduleNextReminder(ctx);
    }
}
