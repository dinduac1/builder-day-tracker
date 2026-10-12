package com.builderday.tracker;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Full-screen wake-up screen shown over the lock screen while the alarm rings. */
public class WakeActivity extends Activity {
    static final String ACTION_CLOSE = "com.builderday.tracker.WAKE_CLOSE";

    private final BroadcastReceiver closer = new BroadcastReceiver() {
        @Override public void onReceive(Context c, Intent i) { finish(); }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        float dp = getResources().getDisplayMetrics().density;

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(0xFF0D1611);
        int pad = (int) (28 * dp);
        root.setPadding(pad, pad, pad, pad);

        TextView eyebrow = text("BUILDER DAY", 13, 0xFF93A598, false);
        eyebrow.setLetterSpacing(0.15f);
        TextView time = text(new SimpleDateFormat("HH:mm", Locale.getDefault()).format(new Date()), 84, 0xFFE4ECE6, true);
        TextView title = text("Wake up", 30, 0xFFE0AD55, true);
        TextView desc = text(Schedule.byId("wake").desc, 17, 0xFFB8C7BC, false);
        desc.setPadding(0, (int) (10 * dp), 0, (int) (36 * dp));

        Button up = button("I'm up", 0xFFE0AD55, 0xFF1B1408, dp);
        up.setOnClickListener(v -> {
            startService(new Intent(this, WakeService.class).setAction(WakeService.ACTION_STOP));
            startActivity(new Intent(this, StartActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            finish();
        });
        Button snooze = button("Snooze " + WakeService.SNOOZE_MIN + " min", 0xFF1A2920, 0xFFE4ECE6, dp);
        snooze.setOnClickListener(v -> {
            startService(new Intent(this, WakeService.class).setAction(WakeService.ACTION_SNOOZE));
            finish();
        });

        root.addView(eyebrow); root.addView(time); root.addView(title); root.addView(desc);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (int) (60 * dp));
        lp.topMargin = (int) (12 * dp);
        root.addView(up, lp);
        root.addView(snooze, new LinearLayout.LayoutParams(lp));
        setContentView(root);

        IntentFilter f = new IntentFilter(ACTION_CLOSE);
        if (android.os.Build.VERSION.SDK_INT >= 33) registerReceiver(closer, f, Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(closer, f);
    }

    private TextView text(String s, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setGravity(Gravity.CENTER);
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        return t;
    }

    private Button button(String s, int bg, int fg, float dp) {
        Button b = new Button(this);
        b.setText(s);
        b.setAllCaps(false);
        b.setTextSize(18);
        b.setTextColor(fg);
        b.setTypeface(Typeface.DEFAULT_BOLD);
        GradientDrawable d = new GradientDrawable();
        d.setColor(bg);
        d.setCornerRadius(14 * dp);
        b.setBackground(d);
        return b;
    }

    @Override
    public void onBackPressed() { /* keep the alarm screen up until I'm up or Snooze */ }

    @Override
    protected void onDestroy() {
        try { unregisterReceiver(closer); } catch (Exception ignored) { }
        super.onDestroy();
    }
}
