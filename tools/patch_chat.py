"""One-off: crew chat. Full-screen chat per crew (groups/{code}/messages), crew activity inline as system lines,
unread badge on the Crew panel, toasts in-app and a push to the crew for each message."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(ROOT, "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rep("</style>\n</head>", r""".chatv{position:fixed;inset:0;z-index:85;background:var(--bg);display:grid;grid-template-rows:auto minmax(0,1fr) auto}
.chatv .ch{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:12px;padding:calc(env(safe-area-inset-top,0px) + 12px) 14px 12px;border-bottom:1px solid var(--line);background:var(--surface)}
.chatv .ch b{display:block;font-family:var(--f-display);font-weight:800;letter-spacing:.08em;text-transform:uppercase;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chatv .ch small{display:block;font-family:var(--f-mono);font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chatv .ch .faces{display:flex}
.chatv .ch .faces span{width:28px;height:28px;border-radius:50%;border:2px solid var(--surface);margin-left:-8px;background:var(--sunk);overflow:hidden;display:grid;place-content:center;font-size:11px;font-weight:700}
.chatv .ch .faces img{width:100%;height:100%;object-fit:cover}
.chatv .cl{overflow-y:auto;padding:12px 12px 10px;display:flex;flex-direction:column;overscroll-behavior:contain}
.chatv .cl .empty{margin:auto;text-align:center;color:var(--muted);max-width:280px;font-size:14px}
.msg{display:grid;grid-template-columns:30px minmax(0,1fr);gap:8px;max-width:84%;align-self:flex-start;margin-top:10px}
.msg.cont{margin-top:3px}.msg.cont .av{visibility:hidden}.msg.cont .nm{display:none}
.msg .av{width:30px;height:30px;border-radius:50%;background:var(--surface);border:1px solid var(--line);overflow:hidden;display:grid;place-content:center;font-weight:700;font-size:12px;align-self:end}
.msg .av img{width:100%;height:100%;object-fit:cover}
.msg .bb{background:var(--surface);border:1px solid var(--line);border-radius:18px 18px 18px 6px;padding:8px 12px 6px;font-size:15px;line-height:1.4;white-space:pre-wrap;overflow-wrap:anywhere;min-width:0}
.msg .nm{font-size:12px;font-weight:700;color:var(--accent);margin-bottom:1px}
.msg time{font-family:var(--f-mono);font-size:10px;color:var(--muted);float:right;margin:7px 0 0 10px}
.msg.me{align-self:flex-end;grid-template-columns:minmax(0,1fr)}.msg.me .av{display:none}
.msg.me .bb{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);border-radius:18px 18px 6px 18px}
.msg.me time{color:rgba(10,12,22,.62)}
.msg .del{grid-column:1 / -1;justify-self:end;border:0;background:none;color:var(--warn);font-family:var(--f-mono);font-size:11px;padding:4px 2px;cursor:pointer}
.sysl{align-self:center;font-size:12.5px;color:var(--muted);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:5px 12px;margin:8px 0 2px;text-align:center;max-width:92%}
.sysl b{color:var(--ink);font-weight:600}
.dsep{align-self:center;font-family:var(--f-mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:16px 0 2px}
.chatv .cc{display:grid;grid-template-columns:minmax(0,1fr) 48px;gap:8px;align-items:end;padding:10px 12px calc(env(safe-area-inset-bottom,0px) + 10px);border-top:1px solid var(--line);background:var(--surface)}
.chatv textarea{font:inherit;font-size:15.5px;resize:none;border:1px solid var(--line);border-radius:22px;padding:12px 16px;background:var(--bg);color:var(--ink);max-height:140px;height:48px;line-height:1.35;outline:none}
.chatv textarea:focus{border-color:var(--accent)}
.chatv .snd{width:48px;height:48px;border-radius:50%;border:0;background:var(--accent);color:var(--accent-ink);display:grid;place-content:center;cursor:pointer}
.chatv .snd:disabled{opacity:.4}
.chatv .snd svg{width:20px;height:20px}
.chatbtn{display:flex;justify-content:space-between;align-items:center;width:100%;margin:12px 0 4px}
.chatbtn .badge{background:var(--warn);color:#fff;border-radius:999px;font-family:var(--f-mono);font-size:11px;font-weight:600;padding:2px 8px;margin-left:8px}
.chatbtn .last{display:block;font-size:12.5px;font-weight:400;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px;text-align:left}
</style>
</head>""")

# crew panel: chat entry with unread count (replaces the small live feed: activity now lives in the chat)
rep('''  if (feedState.events.length) {
    const feed = document.createElement("div"); feed.className = "feed";''', '''  {
    const cb = document.createElement("button"); cb.className = "btn block chatbtn";
    const n = unreadChat(), last = chat.msgs[chat.msgs.length - 1];
    cb.innerHTML = `<span><span>💬 Crew chat</span>${n ? `<span class="badge">${n > 99 ? "99+" : n}</span>` : ""}<span class="last"></span></span><span aria-hidden="true">›</span>`;
    if (last) cb.querySelector(".last").textContent = `${last.uid === fs.uid ? "You" : (last.name || "").split(" ")[0]}: ${last.text}`;
    cb.onclick = openChat;
    box.appendChild(cb);
  }
  if (feedState.events.length) {
    const feed = document.createElement("div"); feed.className = "feed";''')
rep('''    feedState.events.slice(0, 8).forEach(e => {''', '''    feedState.events.slice(0, 3).forEach(e => {''')

# chat follows the same crew as the feed
rep('''function watchFeed(){
  const fs = crewFS(), code = (settings.crews || [])[0] || null;''', '''function watchFeed(){
  watchChat();
  const fs = crewFS(), code = (settings.crews || [])[0] || null;''')
rep('''    feedState.events = snap.docs.map(d => ({id: d.id, ...d.data()}));''', '''    feedState.events = snap.docs.map(d => ({id: d.id, ...d.data()}));
    if (chat.open) drawChat(false);''')

rep("/* =========================================================== crew activity: events, feed, in-app alerts */", r'''/* =========================================================== crew chat */
const chat = {code: null, unsub: null, msgs: [], open: false, since: Date.now(), seen: new Set()};
function watchChat(){
  const fs = crewFS(), code = (settings.crews || [])[0] || null;
  if (chat.code === code && chat.unsub) return;
  if (chat.unsub) { chat.unsub(); chat.unsub = null; }
  chat.code = code; chat.msgs = [];
  if (!fs || !code) return;
  chat.unsub = fs.db.collection("groups").doc(code).collection("messages").orderBy("ts", "desc").limit(200).onSnapshot(snap => {
    chat.msgs = snap.docs.map(d => ({id: d.id, ...d.data()})).reverse();
    snap.docChanges().forEach(ch => {
      const m = ch.doc.data();
      if (ch.type === "added" && m.uid !== fs.uid && m.ts > chat.since && !chat.seen.has(ch.doc.id)) {
        chat.seen.add(ch.doc.id);
        if (!chat.open) alertCrew(`${(m.name || "Someone").split(" ")[0]}: ${m.text}`);
      }
    });
    if (chat.open) { markChatSeen(); drawChat(true); }
    renderCrew();
  }, () => {});
}
const chatSeenAt = () => ((settings.chatSeen || {})[chat.code]) || 0;
function unreadChat(){ const fs = crewFS(); return fs ? chat.msgs.filter(m => m.uid !== fs.uid && m.ts > chatSeenAt()).length : 0; }
function markChatSeen(){
  const last = chat.msgs.length ? chat.msgs[chat.msgs.length - 1].ts : 0;
  if (last > chatSeenAt()) { settings.chatSeen = {...(settings.chatSeen || {}), [chat.code]: last}; saveSettings(); }
}
function sendChat(text){
  const fs = crewFS(), code = chat.code; text = text.trim().slice(0, 1000);
  if (!fs || !code || !text) return;
  const name = (profile().name || fs.user.displayName || "Member").split(" ")[0];
  fs.db.collection("groups").doc(code).collection("messages").add({uid: fs.uid, name, text, ts: Date.now(), at: firebase.firestore.FieldValue.serverTimestamp()})
    .catch(e => toast("Message didn't send: " + (e.message || e)));
  fs.user.getIdToken().then(idToken => fetch("/api/crew/notify", {method: "POST", headers: {"content-type": "application/json"},
    body: JSON.stringify({idToken, code, tag: "chat-" + code, title: `${name} · ${crewState.name || "Crew chat"}`, text})})).catch(() => {});
}
const memberOf = uid => crewState.members.find(m => m.uid === uid) || {};
function avatarHtml(uid, name){
  const m = memberOf(uid), photo = m.photo;
  return photo ? `<img alt="" referrerpolicy="no-referrer" src="${esc(photo)}">` : esc((name || m.name || "?").trim().charAt(0).toUpperCase());
}
function openChat(){
  const fs = crewFS(); if (!fs || !chat.code) return;
  chat.open = true; markChatSeen();
  const el = document.createElement("div"); el.className = "chatv"; el.id = "chatv";
  el.innerHTML = `<div class="ch"><button class="close" aria-label="Back">←</button><div><b></b><small></small></div><div class="faces"></div></div>
    <div class="cl" role="log" aria-live="polite"></div>
    <div class="cc"><textarea rows="1" maxlength="1000" placeholder="Message your crew" aria-label="Message"></textarea><button class="snd" aria-label="Send" disabled>${SHARE_ICONS.send}</button></div>`;
  el.querySelector(".ch b").textContent = crewState.name || "Crew";
  el.querySelector(".ch small").textContent = `${crewState.members.length} member${crewState.members.length === 1 ? "" : "s"} · code ${chat.code}`;
  el.querySelector(".faces").innerHTML = crewState.members.slice(0, 4).map(m => `<span>${avatarHtml(m.uid, m.name)}</span>`).join("");
  document.body.appendChild(el);
  history.pushState({chat: 1}, "");
  window.addEventListener("popstate", closeChatBack);
  el.querySelector(".close").onclick = () => history.back();
  const ta = el.querySelector("textarea"), snd = el.querySelector(".snd");
  const grow = () => { ta.style.height = "48px"; ta.style.height = Math.min(140, ta.scrollHeight + 2) + "px"; snd.disabled = !ta.value.trim(); };
  ta.oninput = grow;
  const send = () => { if (!ta.value.trim()) return; sendChat(ta.value); ta.value = ""; grow(); ta.focus(); };
  snd.onclick = send;
  ta.onkeydown = e => { if (e.key === "Enter" && !e.shiftKey && !("ontouchstart" in window)) { e.preventDefault(); send(); } };
  drawChat(true);
}
function closeChatBack(){ chat.open = false; window.removeEventListener("popstate", closeChatBack); const el = $("chatv"); if (el) el.remove(); renderCrew(); }
function drawChat(stick){
  const el = $("chatv"), fs = crewFS(); if (!el || !fs) return;
  const cl = el.querySelector(".cl"), atBottom = cl.scrollHeight - cl.scrollTop - cl.clientHeight < 80;
  const items = [...chat.msgs.map(m => ({...m, kind: "msg"})), ...feedState.events.map(e => ({...e, kind: "event"}))].sort((a, b) => a.ts - b.ts);
  cl.innerHTML = "";
  if (!items.length) { cl.innerHTML = `<div class="empty">No messages yet. Say something to your crew: a plan, a win, a call-out.</div>`; return; }
  const today = keyOf(new Date()), yest = shift(today, -1);
  let lastDay = null, prev = null;
  items.forEach(it => {
    const d = keyOf(new Date(it.ts));
    if (d !== lastDay) { lastDay = d; prev = null; const s = document.createElement("div"); s.className = "dsep"; s.textContent = d === today ? "Today" : d === yest ? "Yesterday" : fromKey(d).toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short"}); cl.appendChild(s); }
    if (it.kind === "event") {
      const s = document.createElement("div"); s.className = "sysl"; s.innerHTML = "<b></b> <span></span>";
      s.querySelector("b").textContent = it.uid === fs.uid ? "You" : it.name; s.querySelector("span").textContent = it.text;
      cl.appendChild(s); prev = null; return;
    }
    const me = it.uid === fs.uid, cont = prev && prev.uid === it.uid && it.ts - prev.ts < 5 * 60000;
    const m = document.createElement("div"); m.className = "msg" + (me ? " me" : "") + (cont ? " cont" : "");
    m.innerHTML = `<span class="av">${avatarHtml(it.uid, it.name)}</span><div class="bb">${me ? "" : `<div class="nm"></div>`}<span class="tx"></span><time></time></div>`;
    if (!me) m.querySelector(".nm").textContent = it.name || "Member";
    m.querySelector(".tx").textContent = it.text;
    m.querySelector("time").textContent = new Date(it.ts).toLocaleTimeString(undefined, {hour: "2-digit", minute: "2-digit"});
    if (me) m.querySelector(".bb").onclick = () => {
      if (m.querySelector(".del")) return m.querySelector(".del").remove();
      const x = document.createElement("button"); x.className = "del"; x.textContent = "Delete message";
      x.onclick = ev => { ev.stopPropagation(); fs.db.collection("groups").doc(chat.code).collection("messages").doc(it.id).delete().catch(e => toast("Couldn't delete: " + e.message)); };
      m.appendChild(x);
    };
    cl.appendChild(m); prev = it;
  });
  if (stick || atBottom) cl.scrollTop = cl.scrollHeight;
}

/* =========================================================== crew activity: events, feed, in-app alerts */''')
# signing out / switching account closes the chat state
rep('''    unwatchHosted(); photoCache = {};''', '''    unwatchHosted(); photoCache = {};
    if (chat.unsub) { chat.unsub(); chat.unsub = null; } chat.code = null; chat.msgs = [];''')
open(P, "w", encoding="utf-8", newline="\n").write(s)

R = os.path.join(ROOT, "firestore.rules"); r = open(R, encoding="utf-8").read()
a = '''      // Push tokens for crew alerts'''
assert r.count(a) == 1
r = r.replace(a, '''      // Crew chat: members read it; each person posts only as themselves (text up to 1000 characters) and can delete their own.
      match /messages/{id} {
        allow read: if request.auth != null && isMember();
        allow create: if request.auth != null && isMember() && request.resource.data.uid == request.auth.uid
          && request.resource.data.text is string && request.resource.data.text.size() > 0 && request.resource.data.text.size() <= 1000;
        allow delete: if request.auth != null && resource.data.uid == request.auth.uid;
        allow update: if false;
      }

      // Push tokens for crew alerts''')
open(R, "w", encoding="utf-8", newline="\n").write(r)
print("ok")
