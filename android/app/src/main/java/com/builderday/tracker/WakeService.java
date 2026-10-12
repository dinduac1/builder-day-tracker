package com.builderday.tracker;

import android.app.Notification;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;

/**
 * The 05:00 alarm. Plays a looping sound on the alarm stream (rings in silent mode, uses alarm volume),
 * vibrates, and shows a full-screen "Wake up" screen until you tap I'm up or Snooze.
 */
public class WakeService extends Service {
    static final String ACTION_STOP = "com.builderday.tracker.WAKE_STOP";
    static final String ACTION_SNOOZE = "com.builderday.tracker.WAKE_SNOOZE";
    static final int NOTIF_ID = 500, SNOOZE_MIN = 5;
    private static final long AUTO_STOP_MS = 10 * 60 * 1000L;

    private MediaPlayer player;
    private Vibrator vibrator;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : null;
        if (ACTION_SNOOZE.equals(action)) {
            Scheduler.scheduleWake(this, System.currentTimeMillis() + SNOOZE_MIN * 60_000L);
            stopSelf();
            return START_NOT_STICKY;
        }
        if (ACTION_STOP.equals(action)) {
            Scheduler.scheduleWake(this, Schedule.nextAt(System.currentTimeMillis(), Schedule.byId("wake").startMin()));
            stopSelf();
            return START_NOT_STICKY;
        }

        Notifs.createChannels(this);
        Notification n = buildNotification();
        if (Build.VERSION.SDK_INT >= 29) startForeground(NOTIF_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);
        else startForeground(NOTIF_ID, n);
        startRinging();
        handler.postDelayed(this::stopSelf, AUTO_STOP_MS);
        return START_NOT_STICKY;
    }

    private Notification buildNotification() {
        PendingIntent full = PendingIntent.getActivity(this, 501,
                new Intent(this, WakeActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_USER_ACTION),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent up = PendingIntent.getService(this, 502, new Intent(this, WakeService.class).setAction(ACTION_STOP),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent snooze = PendingIntent.getService(this, 503, new Intent(this, WakeService.class).setAction(ACTION_SNOOZE),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Schedule.Block w = Schedule.byId("wake");
        return new Notification.Builder(this, Notifs.CH_WAKE)
                .setSmallIcon(R.drawable.ic_stat)
                .setColor(0xFFE0AD55)
                .setContentTitle("Wake up · " + w.start)
                .setContentText(w.desc)
                .setCategory(Notification.CATEGORY_ALARM)
                .setFullScreenIntent(full, true)
                .setContentIntent(full)
                .setOngoing(true)
                .addAction(new Notification.Action.Builder(null, "I'm up", up).build())
                .addAction(new Notification.Action.Builder(null, "Snooze " + SNOOZE_MIN + " min", snooze).build())
                .build();
    }

    private void startRinging() {
        try {
            player = new MediaPlayer();
            player.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
            player.setDataSource(this, Notifs.sound(this, "wake_alarm"));
            player.setLooping(true);
            player.prepare();
            player.start();
        } catch (Exception ignored) { }
        vibrator = getSystemService(Vibrator.class);
        if (vibrator != null && vibrator.hasVibrator())
            vibrator.vibrate(VibrationEffect.createWaveform(new long[]{0, 700, 500, 700, 1200}, 0));
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (player != null) { try { player.stop(); } catch (Exception ignored) { } player.release(); player = null; }
        if (vibrator != null) vibrator.cancel();
        sendBroadcast(new Intent(WakeActivity.ACTION_CLOSE).setPackage(getPackageName()));
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
