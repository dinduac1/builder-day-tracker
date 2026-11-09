package com.builderday.tracker;

import androidx.annotation.NonNull;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

import java.util.Map;

/** Crew alerts pushed through Firebase Cloud Messaging ("Ada finished her outdoor workout · Day 12"). */
public class CrewMessagingService extends FirebaseMessagingService {
    static final String PREFS = "fcm", KEY_TOKEN = "token";

    @Override
    public void onNewToken(@NonNull String token) {
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(KEY_TOKEN, token).apply();
    }

    @Override
    public void onMessageReceived(@NonNull RemoteMessage message) {
        Map<String, String> d = message.getData();
        String title = d.containsKey("title") ? d.get("title") : "Your crew";
        String body = d.containsKey("body") ? d.get("body") : "";
        String tag = d.containsKey("tag") ? d.get("tag") : "crew";
        Notifs.createChannels(this);
        Notifs.postCrew(this, Math.abs((tag + body).hashCode()) % 100000 + 10000, title, body);
    }
}
