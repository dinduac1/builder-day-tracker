package com.builderday.tracker;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Alarms are cleared on reboot, app update and clock changes; put them back. */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        Notifs.createChannels(ctx);
        Scheduler.scheduleAll(ctx);
    }
}
