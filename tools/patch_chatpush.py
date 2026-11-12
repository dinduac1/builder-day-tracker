"""One-off: chat message notifications. Own channel + sound (s_message), grouped per crew, tap opens the chat;
web push opens the chat too; a Chat messages switch in Notification settings."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
J = os.path.join(ROOT, "android", "app", "src", "main", "java", "com", "builderday", "tracker")
def edit(path, pairs):
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (os.path.basename(path), s.count(a), a[:70])
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="\n").write(s)

edit(os.path.join(J, "NotifPrefs.java"), [
    ('        {"s_train", "Punch"},', '        {"s_message", "Message (ORDO)"}, {"s_train", "Punch"},'),
    ('    static final String[] EXTRAS = {"warn", "nag", "crew", "wake"};', '    static final String[] EXTRAS = {"warn", "nag", "crew", "wake", "chat"};'),
    ('        if ("crew".equals(key)) return "s_connect";', '        if ("crew".equals(key)) return "s_connect";\n        if ("chat".equals(key)) return "s_message";'),
    ('            o.put("crewSound", soundOf(ctx, "crew"));', '            o.put("crewSound", soundOf(ctx, "crew"));\n            o.put("chatSound", soundOf(ctx, "chat"));'),
])
edit(os.path.join(J, "Notifs.java"), [
    ('    static String crewChannel(Context ctx) { return "crew_" + NotifPrefs.soundOf(ctx, "crew"); }',
     '''    static String crewChannel(Context ctx) { return "crew_" + NotifPrefs.soundOf(ctx, "crew"); }
    static String chatChannel(Context ctx) { return "chat_" + NotifPrefs.soundOf(ctx, "chat"); }'''),
    ('''        make(nm, ctx, crewChannel(ctx), "Crew", "When someone in your crew finishes a goal or a day", NotifPrefs.soundOf(ctx, "crew"), notif, keep);''',
     '''        make(nm, ctx, crewChannel(ctx), "Crew", "When someone in your crew finishes a goal or a day", NotifPrefs.soundOf(ctx, "crew"), notif, keep);
        make(nm, ctx, chatChannel(ctx), "Crew chat", "New messages, photos and voice notes from your crew", NotifPrefs.soundOf(ctx, "chat"), new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_COMMUNICATION_INSTANT).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build(), keep);'''),
    ('''            if ((id.startsWith("blk_") || id.startsWith("block_") || id.startsWith("warn_") || id.startsWith("crew_")) && !keep.contains(id))''',
     '''            if ((id.startsWith("blk_") || id.startsWith("block_") || id.startsWith("warn_") || id.startsWith("crew_") || id.startsWith("chat_")) && !keep.contains(id))'''),
    ('''    static PendingIntent openTracker(Context ctx, int rc) {''', '''    /** Tapping opens ORDO straight into the crew chat. */
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

    static PendingIntent openTracker(Context ctx, int rc) {'''),
])
edit(os.path.join(J, "CrewMessagingService.java"), [
    ('''        Notifs.postCrew(this, Math.abs((tag + body).hashCode()) % 100000 + 10000, title, body);''',
     '''        if (tag.startsWith("chat-")) Notifs.postChat(this, tag, title, body);
        else Notifs.postCrew(this, Math.abs((tag + body).hashCode()) % 100000 + 10000, title, body);'''),
])
edit(os.path.join(J, "StartActivity.java"), [
    ('''        startActivity(new Intent(this, TrackerActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP));''',
     '''        Intent t = new Intent(this, TrackerActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        String open = getIntent() != null ? getIntent().getStringExtra("open") : null;   // e.g. a chat notification
        if (open != null) t.putExtra("open", open);
        startActivity(t);'''),
])
edit(os.path.join(J, "TrackerActivity.java"), [
    ('''    private WebView splash;''', '''    private WebView splash;
    private String pendingOpen;                                // "chat" when opened from a chat notification
    private boolean pageReady;'''),
    ('''        if (state != null) web.restoreState(state);''', '''        pendingOpen = getIntent().getStringExtra("open");
        if (state != null) web.restoreState(state);'''),
    ('''        super.onNewIntent(intent);
        setIntent(intent);''', '''        super.onNewIntent(intent);
        setIntent(intent);
        String open = intent.getStringExtra("open");
        if (open != null) { pendingOpen = open; if (pageReady) deliverOpen(); }'''),
    ('''        @JavascriptInterface public void appReady() { runOnUiThread(TrackerActivity.this::hideSplash); }''',
     '''        @JavascriptInterface public void appReady() { runOnUiThread(() -> { hideSplash(); pageReady = true; deliverOpen(); }); }'''),
    ('''    private void hideSplash() {''', '''    private void deliverOpen() {
        if (pendingOpen == null) return;
        js("window.__ordoOpen && window.__ordoOpen(" + JSONObject.quote(pendingOpen) + ")");
        pendingOpen = null;
    }

    private void hideSplash() {'''),
])

W = os.path.join(ROOT, "worker.js")
edit(W, [('''  const msg = {title: String(title || "Your crew").slice(0, 80), body: text.slice(0, 240), tag: tag || "crew-" + code, url: "/"};''',
          '''  const t = tag || "crew-" + code;
  const msg = {title: String(title || "Your crew").slice(0, 80), body: text.slice(0, 240), tag: t, url: t.startsWith("chat-") ? "/?open=chat" : "/"};''')])

SW = os.path.join(ROOT, "sw.js")
edit(SW, [('''    for (const w of wins) if ("focus" in w) return w.focus();
    return self.clients.openWindow(e.notification.data && e.notification.data.url || "./");''',
           '''    const url = (e.notification.data && e.notification.data.url) || "./";
    for (const w of wins) if ("focus" in w) { await w.focus(); if (url.includes("open=chat")) w.postMessage({open: "chat"}); return; }
    return self.clients.openWindow(url);''')])

P = os.path.join(ROOT, "index.html")
edit(P, [
    ('''/* =========================================================== crew activity: events, feed, in-app alerts */''',
     '''/** Open something on request: a chat notification was tapped (app, or web push). Waits for the crew to load. */
window.__ordoOpen = (what, tries = 0) => {
  if (what !== "chat") return;
  if (crewFS() && chat.code && crewState.members.length) { if (!chat.open) openChat(); return; }
  if (tries < 20) setTimeout(() => window.__ordoOpen(what, tries + 1), 500);
};
if ("serviceWorker" in navigator) navigator.serviceWorker.addEventListener("message", e => { if (e.data && e.data.open) window.__ordoOpen(e.data.open); });
if (/[?&]open=chat\\b/.test(location.search)) { history.replaceState(null, "", location.pathname); window.__ordoOpen("chat"); }

/* =========================================================== crew activity: events, feed, in-app alerts */'''),
    ('''    const c = nrow("Crew alerts", "When someone in your crew finishes something", X.crew !== false, on => set("crew", on));''',
     '''    const ch = nrow("Chat messages", "New messages, photos and voice notes", X.chat !== false, on => set("chat", on));
    if (X.chat !== false) soundPicker(ch, P.sounds || [], P.chatSound || "s_message", v => snd("chat", v));
    box.appendChild(ch);
    const c = nrow("Crew alerts", "When someone in your crew finishes something", X.crew !== false, on => set("crew", on));'''),
    ('''  drawReply(); drawNeedHandle();
  drawChat(true);''', '''  drawReply(); drawNeedHandle();
  if (!NATIVE && "Notification" in window && Notification.permission === "default") {
    const nb = document.createElement("button"); nb.className = "dsep"; nb.style.cssText = "align-self:stretch;margin:6px 8px;cursor:pointer;border:0;color:var(--accent)";
    nb.textContent = "🔔 Get notified when your crew messages you";
    nb.onclick = async () => { const m = await enableWebCrewAlerts(); nb.textContent = m || "Notifications are on."; setTimeout(() => nb.remove(), 1800); };
    el.querySelector(".cl").before(nb);
  }
  drawChat(true);'''),
])
print("ok")
