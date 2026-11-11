"""One-off: Telegram-style crew chat. @handles with mentions, photos, videos, voice notes (hold to record),
reply / copy / delete, on-brand chat icon."""
import os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(ROOT, "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

# ---- CSS: replace the first chat styles
i = s.index(".chatv{position:fixed;inset:0;z-index:85;"); j = s.index("</style>", i)
s = s[:i] + r""".chatv{position:fixed;inset:0;z-index:85;background:#08090C;display:grid;grid-template-rows:auto minmax(0,1fr) auto;color:var(--ink)}
.chatv::before{content:"";position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse at 20% 0%,rgba(124,139,255,.10),transparent 55%),radial-gradient(ellipse at 100% 100%,rgba(124,139,255,.06),transparent 50%)}
.chatv > *{position:relative}
.chatv .ch{display:grid;grid-template-columns:auto auto minmax(0,1fr);align-items:center;gap:12px;padding:calc(env(safe-area-inset-top,0px) + 10px) 12px 10px;border-bottom:1px solid var(--line);background:rgba(17,19,24,.92);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);z-index:3}
.chatv .back{width:40px;height:40px;border-radius:50%;border:0;background:none;color:var(--ink);font-size:22px;cursor:pointer}
.chatv .cico{width:42px;height:42px}
.chatv .ch b{display:block;font-family:var(--f-display);font-weight:800;letter-spacing:.06em;text-transform:uppercase;font-size:19px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chatv .ch small{display:block;font-size:12.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chatv .cl{overflow-y:auto;padding:10px 10px 12px;display:flex;flex-direction:column;overscroll-behavior:contain}
.chatv .cl .empty{margin:auto;text-align:center;color:var(--muted);max-width:280px;font-size:14px;display:grid;gap:12px;justify-items:center}
.msg{display:grid;grid-template-columns:32px minmax(0,1fr);gap:7px;max-width:86%;align-self:flex-start;margin-top:10px;transition:background .6s}
.msg.flash .bb{box-shadow:0 0 0 2px var(--accent)}
.msg.cont{margin-top:3px}.msg.cont .av{visibility:hidden}.msg.cont .nm{display:none}
.msg .av{width:32px;height:32px;border-radius:50%;background:#1a1d26;overflow:hidden;display:grid;place-content:center;font-weight:700;font-size:13px;align-self:end;color:var(--ink)}
.msg .av img{width:100%;height:100%;object-fit:cover}
.msg .bb{background:#171a22;border-radius:18px 18px 18px 6px;padding:7px 11px 6px;font-size:15px;line-height:1.38;overflow-wrap:anywhere;min-width:0;user-select:text;-webkit-user-select:text}
.msg.cont .bb{border-radius:6px 18px 18px 6px}
.msg .nm{font-size:13px;font-weight:700;color:var(--accent);margin-bottom:2px}
.msg .nm small{font-weight:500;color:var(--muted);margin-left:6px;font-size:11.5px}
.msg .tx{white-space:pre-wrap}
.msg time{font-family:var(--f-mono);font-size:10px;color:var(--muted);float:right;margin:8px 0 -2px 10px;line-height:1}
.msg.me{align-self:flex-end;grid-template-columns:minmax(0,1fr)}.msg.me .av{display:none}
.msg.me .bb{background:linear-gradient(160deg,#8794FF,#6F7EF5);color:#0A0C16;border-radius:18px 18px 6px 18px}
.msg.me.cont .bb{border-radius:18px 6px 6px 18px}
.msg.me time{color:rgba(10,12,22,.6)}
.msg.me .mention{color:#0A0C16;background:rgba(255,255,255,.28)}
.mention{color:var(--accent);font-weight:600;border-radius:5px;padding:0 2px}
.mention.mine{background:rgba(124,139,255,.18)}
.msg a.lnk{color:inherit;text-decoration:underline;text-underline-offset:2px}
.msg .rq{display:block;border-left:3px solid var(--accent);background:rgba(124,139,255,.1);border-radius:6px;padding:4px 8px;margin:2px 0 6px;font-size:13px;cursor:pointer;max-width:100%;overflow:hidden}
.msg.me .rq{border-color:#0A0C16;background:rgba(10,12,22,.12)}
.msg .rq b{display:block;font-size:12px}.msg .rq span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.8}
.msg .media{margin:-3px -7px 4px;border-radius:14px;overflow:hidden;background:#000;position:relative;max-width:300px}
.msg .media img,.msg .media video{display:block;width:100%;max-height:360px;object-fit:cover;cursor:zoom-in;background:#0d0f14}
.msg .media video{cursor:default;object-fit:contain}
.msg .media .up{position:absolute;inset:0;display:grid;place-content:center;background:rgba(0,0,0,.45);color:#fff;font-family:var(--f-mono);font-size:12px}
.msg .media .up.err{background:rgba(120,20,20,.6);padding:10px;text-align:center}
.msg .tx:empty{display:none}
.vn{display:grid;grid-template-columns:40px minmax(0,1fr);gap:10px;align-items:center;min-width:220px;padding:2px 0}
.vn .vp{width:40px;height:40px;border-radius:50%;border:0;background:var(--accent);color:#0A0C16;display:grid;place-content:center;cursor:pointer}
.msg.me .vn .vp{background:#0A0C16;color:#8794FF}
.vn .vp svg{width:16px;height:16px}
.vn .vw{display:flex;align-items:center;gap:2px;height:28px}
.vn .vw i{flex:1;min-width:2px;border-radius:2px;background:currentColor;opacity:.35}
.vn .vw i.on{opacity:1}
.vn .vt{grid-column:2;font-family:var(--f-mono);font-size:10.5px;opacity:.7;margin-top:-4px}
.sysl{align-self:center;font-size:12.5px;color:var(--muted);background:rgba(23,26,34,.85);border-radius:999px;padding:5px 12px;margin:8px 0 2px;text-align:center;max-width:92%}
.sysl b{color:var(--ink);font-weight:600}
.dsep{align-self:center;font-size:12px;font-weight:600;color:var(--ink);background:rgba(23,26,34,.85);border-radius:999px;padding:4px 12px;margin:14px 0 4px}
.chatv .cc{display:grid;gap:6px;padding:8px 8px calc(env(safe-area-inset-bottom,0px) + 8px);background:rgba(17,19,24,.96);border-top:1px solid var(--line);z-index:3}
.chatv .crow{display:grid;grid-template-columns:44px minmax(0,1fr) 48px;gap:6px;align-items:end}
.chatv .ib{width:44px;height:44px;border-radius:50%;border:0;background:none;color:var(--muted);display:grid;place-content:center;cursor:pointer}
.chatv .ib svg{width:24px;height:24px}
.chatv textarea{font:inherit;font-size:16px;resize:none;border:0;border-radius:22px;padding:11px 16px;background:#1a1d26;color:var(--ink);max-height:140px;height:44px;line-height:1.35;outline:none}
.chatv .snd{width:48px;height:48px;border-radius:50%;border:0;background:var(--accent);color:#0A0C16;display:grid;place-content:center;cursor:pointer;touch-action:none;transition:transform .15s}
.chatv .snd svg{width:22px;height:22px}
.chatv .snd.rec{transform:scale(1.35);background:#FF6E6A;color:#fff}
.chatv .replybar,.chatv .rec{display:grid;grid-template-columns:4px minmax(0,1fr) 36px;gap:10px;align-items:center;padding:4px 6px}
.chatv .replybar i{align-self:stretch;background:var(--accent);border-radius:2px}
.chatv .replybar b{display:block;color:var(--accent);font-size:13px}.chatv .replybar span{display:block;font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chatv .replybar button{border:0;background:none;color:var(--muted);font-size:18px;cursor:pointer}
.chatv .rec{grid-template-columns:auto auto minmax(0,1fr);height:44px;padding:0 14px;font-family:var(--f-mono);font-size:14px;position:absolute;left:8px;right:66px;bottom:calc(env(safe-area-inset-bottom,0px) + 10px);background:rgba(17,19,24,.98)}
.chatv .rec .dotr{width:10px;height:10px;border-radius:50%;background:#FF6E6A;animation:blink 1s infinite}
.chatv .rec .hint{justify-self:end;color:var(--muted);font-family:var(--f-body);font-size:13px}
@keyframes blink{50%{opacity:.2}}
.chatv .mentions{display:grid;background:#171a22;border:1px solid var(--line);border-radius:14px;overflow:hidden;max-height:220px;overflow-y:auto}
.chatv .mentions button{display:grid;grid-template-columns:30px minmax(0,1fr);gap:10px;align-items:center;padding:8px 12px;border:0;background:none;color:var(--ink);text-align:left;cursor:pointer;font:inherit}
.chatv .mentions button:hover{background:#1f2330}
.chatv .mentions .av{width:30px;height:30px;border-radius:50%;background:#262a36;overflow:hidden;display:grid;place-content:center;font-weight:700;font-size:12px}
.chatv .mentions .av img{width:100%;height:100%;object-fit:cover}
.chatv .mentions small{color:var(--muted);margin-left:6px}
.chatv .needhandle{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;padding:4px}
.chatv .needhandle input{font:inherit;font-size:15px;padding:11px 14px;border-radius:14px;border:1px solid var(--line);background:#1a1d26;color:var(--ink)}
.chatv .needhandle p{grid-column:1 / -1;margin:0;font-size:13px;color:var(--muted)}
.csheet{position:absolute;inset:0;z-index:6;background:rgba(0,0,0,.55);display:flex;align-items:flex-end}
.csheet .card{width:100%;background:#14161c;border-radius:22px 22px 0 0;padding:10px 10px calc(env(safe-area-inset-bottom,0px) + 12px);display:grid;gap:2px}
.csheet .card button{display:grid;grid-template-columns:28px minmax(0,1fr);gap:14px;align-items:center;padding:14px 12px;border:0;background:none;color:var(--ink);font:inherit;font-size:16px;text-align:left;border-radius:14px;cursor:pointer}
.csheet .card button:hover{background:#1c1f28}
.csheet .card button svg{width:24px;height:24px;color:var(--accent)}
.csheet .card button.danger,.csheet .card button.danger svg{color:var(--warn)}
.cprev{position:absolute;inset:0;z-index:7;background:#000;display:grid;grid-template-rows:auto minmax(0,1fr) auto}
.cprev .pt{display:flex;justify-content:space-between;align-items:center;padding:calc(env(safe-area-inset-top,0px) + 10px) 12px 10px;color:#fff}
.cprev .pt button{border:0;background:none;color:#fff;font-size:22px;cursor:pointer}
.cprev .pm{display:grid;place-content:center;overflow:hidden;padding:8px}
.cprev .pm img,.cprev .pm video{max-width:100%;max-height:70vh;border-radius:10px}
.cprev .pm .many{color:#fff;font-family:var(--f-mono);font-size:12px;text-align:center;margin-top:8px}
.cprev .pb{display:grid;grid-template-columns:minmax(0,1fr) 52px;gap:8px;padding:10px 10px calc(env(safe-area-inset-bottom,0px) + 10px);background:rgba(17,19,24,.96)}
.cprev .pb input{font:inherit;font-size:16px;border:0;border-radius:22px;padding:13px 16px;background:#1a1d26;color:#F3F1EC;outline:none}
.cprev .pb button{width:52px;height:52px;border-radius:50%;border:0;background:var(--accent);color:#0A0C16;display:grid;place-content:center;cursor:pointer}
.cview{position:absolute;inset:0;z-index:8;background:#000;display:grid;grid-template-rows:auto minmax(0,1fr)}
.cview .pt{display:flex;justify-content:space-between;align-items:center;padding:calc(env(safe-area-inset-top,0px) + 10px) 12px 10px;color:#fff}
.cview .pt button{border:0;background:rgba(255,255,255,.1);color:#fff;border-radius:999px;padding:8px 14px;font:inherit;font-size:14px;cursor:pointer}
.cview img{max-width:100%;max-height:100%;margin:auto;object-fit:contain;align-self:center;justify-self:center}
.chatbtn{display:grid!important;grid-template-columns:44px minmax(0,1fr) auto;gap:12px;align-items:center;width:100%;margin:12px 0 4px;padding:10px 14px!important;border-radius:18px!important;text-align:left}
.chatbtn .cico{width:44px;height:44px}
.chatbtn b{display:block;font-size:15px}
.chatbtn .last{display:block;font-size:13px;font-weight:400;color:var(--muted);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chatbtn .badge{background:var(--accent);color:#0A0C16;border-radius:999px;font-family:var(--f-mono);font-size:12px;font-weight:700;min-width:24px;height:24px;display:grid;place-content:center;padding:0 7px}
.pfhandle{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;border:1px solid var(--line);border-radius:14px;background:var(--bg);padding-left:14px}
.pfhandle span{color:var(--muted);font-size:17px}
.pfhandle input{border:0!important;background:none!important;padding-left:4px!important}
""" + s[j:]

# ---- crew rows carry the handle
rep('''    city: (profile().city || "").slice(0, 40), headline: (profile().headline || "").slice(0, 80),''',
    '''    city: (profile().city || "").slice(0, 40), headline: (profile().headline || "").slice(0, 80), handle: profile().handle || "",''')

# ---- profile form: @handle
rep('''    <label class="fl" for="pfCity">City</label>''', '''    <label class="fl" for="pfHandle">Handle</label><div class="pfhandle"><span>@</span><input class="tx" id="pfHandle" maxlength="20" placeholder="yourname" autocapitalize="off" autocomplete="off" spellcheck="false"></div>
    <label class="fl" for="pfCity">City</label>''')
rep('''  nm.value = p.name || (me && me.user.displayName ? me.user.displayName.split(" ")[0] : ""); ct.value = p.city || ""; hd.value = p.headline || "";''',
    '''  nm.value = p.name || (me && me.user.displayName ? me.user.displayName.split(" ")[0] : ""); ct.value = p.city || ""; hd.value = p.headline || "";
  const hn = box.querySelector("#pfHandle"); hn.value = p.handle || "";
  if (!hn.value) hn.placeholder = suggestHandle();
  hn.oninput = () => { hn.value = hn.value.toLowerCase().replace(/[^a-z0-9_]/g, ""); };''')
rep('''  sv.onclick = () => {
    if (!nm.value.trim()) { box.querySelector("#pfMsg").textContent = "Add your name so your crew knows who you are."; nm.focus(); return; }
    settings.profile = {...profile(), name: nm.value.trim(), city: ct.value.trim(), headline: hd.value.trim(), photo};''', '''  sv.onclick = async () => {
    const msg = box.querySelector("#pfMsg");
    if (!nm.value.trim()) { msg.textContent = "Add your name so your crew knows who you are."; nm.focus(); return; }
    const want = hn.value || (crewFS() && !profile().handle ? "" : "");
    if (want && want !== (profile().handle || "")) {
      sv.disabled = true; msg.textContent = "Checking @" + want + "…";
      try { await claimHandle(want); msg.textContent = ""; } catch(e) { msg.textContent = e.message; sv.disabled = false; hn.focus(); return; }
      sv.disabled = false;
    }
    settings.profile = {...profile(), name: nm.value.trim(), city: ct.value.trim(), headline: hd.value.trim(), photo};''')

# ---- crew panel chat button: on-brand icon
rep('''    const cb = document.createElement("button"); cb.className = "btn block chatbtn";
    const n = unreadChat(), last = chat.msgs[chat.msgs.length - 1];
    cb.innerHTML = `<span><span>💬 Crew chat</span>${n ? `<span class="badge">${n > 99 ? "99+" : n}</span>` : ""}<span class="last"></span></span><span aria-hidden="true">›</span>`;
    if (last) cb.querySelector(".last").textContent = `${last.uid === fs.uid ? "You" : (last.name || "").split(" ")[0]}: ${last.text}`;''',
'''    const cb = document.createElement("button"); cb.className = "btn block chatbtn";
    const n = unreadChat(), last = chat.msgs[chat.msgs.length - 1];
    cb.innerHTML = `${CHAT_ICON}<span><b>Crew chat</b><span class="last">Messages, photos, voice notes</span></span>${n ? `<span class="badge">${n > 99 ? "99+" : n}</span>` : `<span aria-hidden="true" style="color:var(--muted);font-size:22px">›</span>`}`;
    if (last) cb.querySelector(".last").textContent = `${last.uid === fs.uid ? "You" : (last.name || "").split(" ")[0]}: ${msgPreview(last)}`;''')

# ---- the chat module
i = s.index("/* =========================================================== crew chat */"); j = s.index("/* =========================================================== crew activity: events, feed, in-app alerts */")
s = s[:i] + r'''/* =========================================================== crew chat */
const chat = {code: null, unsub: null, msgs: [], open: false, since: Date.now(), seen: new Set(), reply: null, pending: []};
const HANDLE_RE = /^[a-z0-9_]{3,20}$/;
const CHAT_ICON = '<svg class="cico" viewBox="0 0 48 48" aria-hidden="true"><rect width="48" height="48" rx="14" fill="#111318"/><path d="M24 11.5a12.5 12.5 0 1 1-6.9 22.9L11.5 36l1.7-5.4A12.5 12.5 0 0 1 24 11.5z" fill="none" stroke="#F3F1EC" stroke-width="3.2" stroke-linejoin="round"/><path d="M28.6 12.4a12.5 12.5 0 0 1 6.9 7.1" fill="none" stroke="#7C8BFF" stroke-width="3.6" stroke-linecap="round"/><circle cx="19" cy="24" r="1.9" fill="#F3F1EC"/><circle cx="24.5" cy="24" r="1.9" fill="#F3F1EC"/><circle cx="30" cy="24" r="1.9" fill="#7C8BFF"/></svg>';
const CI = {
  clip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m20.5 11.5-8.6 8.6a5.4 5.4 0 0 1-7.6-7.6l8.6-8.6a3.6 3.6 0 0 1 5.1 5.1l-8.6 8.6a1.8 1.8 0 0 1-2.5-2.5l7.9-7.9"/></svg>',
  mic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/></svg>',
  send: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.4 20.4 21 12 3.4 3.6l-.1 6.5L15 12 3.3 13.9z"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>',
  pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4.5" width="4" height="15" rx="1"/><rect x="14" y="4.5" width="4" height="15" rx="1"/></svg>',
  photo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.8"/><path d="m4 18 5-5 4 4 3-3 4 4"/></svg>',
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3 8h4l2-3h6l2 3h4v12H3z"/><circle cx="12" cy="13.5" r="3.8"/></svg>',
  video: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="3" y="6" width="13" height="12" rx="2.5"/><path d="m16 10.5 5-3v9l-5-3z"/></svg>',
  reply: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 7 4 12l6 5"/><path d="M4 12h10a6 6 0 0 1 6 6v1"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/></svg>',
  del: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  save: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
};
const myHandle = () => profile().handle || "";
const suggestHandle = () => ((profile().name || (crewFS() && crewFS().user.displayName) || "member").toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 14) || "member");
/** Claim a unique @handle (handles/{name} → uid), releasing the old one. */
async function claimHandle(h){
  h = String(h || "").toLowerCase().replace(/^@/, "");
  if (!HANDLE_RE.test(h)) throw new Error("Handles are 3–20 letters, numbers or _.");
  const fs = crewFS();
  if (fs) {
    const ref = fs.db.collection("handles").doc(h), old = myHandle();
    await fs.db.runTransaction(async t => {
      const d = await t.get(ref);
      if (d.exists && d.data().uid !== fs.uid) throw new Error(`@${h} is taken. Try another.`);
      t.set(ref, {uid: fs.uid, at: Date.now()});
      if (old && old !== h) t.delete(fs.db.collection("handles").doc(old));
    });
  }
  settings.profile = {...profile(), handle: h}; saveSettings(); crewState.last = ""; pushCrew();
  return h;
}
function watchChat(){
  const fs = crewFS(), code = (settings.crews || [])[0] || null;
  if (chat.code === code && chat.unsub) return;
  if (chat.unsub) { chat.unsub(); chat.unsub = null; }
  chat.code = code; chat.msgs = [];
  if (!fs || !code) return;
  chat.unsub = fs.db.collection("groups").doc(code).collection("messages").orderBy("ts", "desc").limit(300).onSnapshot(snap => {
    chat.msgs = snap.docs.map(d => ({id: d.id, ...d.data()})).reverse();
    snap.docChanges().forEach(ch => {
      const m = ch.doc.data();
      if (ch.type === "added" && m.uid !== fs.uid && m.ts > chat.since && !chat.seen.has(ch.doc.id)) {
        chat.seen.add(ch.doc.id);
        if (!chat.open) alertCrew(mentionsMe(m.text) ? `${firstName(m.name)} mentioned you: ${msgPreview(m)}` : `${firstName(m.name)}: ${msgPreview(m)}`);
      }
    });
    if (chat.open) { markChatSeen(); drawChat(false); }
    renderCrew();
  }, () => {});
}
const firstName = n => (n || "Someone").split(" ")[0];
const mentionsMe = t => !!myHandle() && new RegExp(`@${myHandle()}\\b`, "i").test(t || "");
function msgPreview(m){
  if (m.media) return ({image: "📷 Photo", video: "🎥 Video", audio: `🎤 Voice note${m.media.dur ? " " + fmtSec(Math.round(m.media.dur)) : ""}`}[m.media.type] || "📎 File") + (m.text ? " · " + m.text : "");
  return m.text || "";
}
const chatSeenAt = () => ((settings.chatSeen || {})[chat.code]) || 0;
function unreadChat(){ const fs = crewFS(); return fs ? chat.msgs.filter(m => m.uid !== fs.uid && m.ts > chatSeenAt()).length : 0; }
function markChatSeen(){
  const last = chat.msgs.length ? chat.msgs[chat.msgs.length - 1].ts : 0;
  if (last > chatSeenAt()) { settings.chatSeen = {...(settings.chatSeen || {}), [chat.code]: last}; saveSettings(); }
}
/** Write one message (text and/or media), then alert the crew. */
async function postMessage(fields){
  const fs = crewFS(), code = chat.code; if (!fs || !code) return;
  const name = firstName(profile().name || fs.user.displayName || "Member");
  const doc = {uid: fs.uid, name, handle: myHandle(), ts: Date.now(), at: firebase.firestore.FieldValue.serverTimestamp(), text: (fields.text || "").trim().slice(0, 1000)};
  if (fields.media) doc.media = fields.media;
  if (chat.reply) { doc.replyTo = chat.reply; chat.reply = null; drawReply(); }
  await fs.db.collection("groups").doc(code).collection("messages").add(doc).catch(e => toast("Message didn't send: " + (e.message || e)));
  fs.user.getIdToken().then(idToken => fetch("/api/crew/notify", {method: "POST", headers: {"content-type": "application/json"},
    body: JSON.stringify({idToken, code, tag: "chat-" + code, title: `${name} · ${crewState.name || "Crew chat"}`, text: msgPreview(doc)})})).catch(() => {});
}
function uploadMedia(blob, type, onProgress){
  return new Promise(async (res, rej) => {
    const fs = crewFS(); if (!fs) return rej(new Error("Sign in first."));
    const tok = await fs.user.getIdToken().catch(() => null);
    const x = new XMLHttpRequest();
    x.open("POST", `/api/media?code=${chat.code}`);
    x.setRequestHeader("authorization", "Bearer " + tok); x.setRequestHeader("content-type", type);
    x.upload.onprogress = e => { if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total); };
    x.onload = () => { let j = {}; try { j = JSON.parse(x.responseText || "{}"); } catch(e){} x.status === 200 ? res(j) : rej(new Error(j.error || `Upload failed (${x.status})`)); };
    x.onerror = () => rej(new Error("Upload failed. Check your connection."));
    x.send(blob);
  });
}
/** Show it in the chat straight away (with progress), upload, then post the message. */
async function sendMedia(blob, kind, extra, caption){
  const p = {pid: "p" + Date.now() + Math.random(), kind, local: URL.createObjectURL(blob), progress: 0, text: caption || "", extra, ts: Date.now()};
  chat.pending.push(p); drawChat(true);
  try {
    const r = await uploadMedia(blob, blob.type, f => { p.progress = f; const el = document.querySelector(`[data-pid="${p.pid}"] .up`); if (el) el.textContent = Math.round(f * 100) + "%"; });
    await postMessage({text: caption, media: {type: kind, key: r.key, mime: blob.type, size: blob.size, ...extra}});
    chat.pending = chat.pending.filter(x => x !== p);
  } catch(e) { p.error = e.message; }
  drawChat(true);
}
async function prepImage(file){
  if (file.type === "image/gif" && file.size < 8e6) { const b = await createImageBitmap(file).catch(() => null); return {blob: file, w: b ? b.width : 0, h: b ? b.height : 0}; }
  const bmp = await createImageBitmap(file), k = Math.min(1, 1920 / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas"); c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k);
  const x = c.getContext("2d"); x.imageSmoothingQuality = "high"; x.drawImage(bmp, 0, 0, c.width, c.height);
  const blob = await new Promise(r => c.toBlob(r, "image/jpeg", .88));
  return {blob, w: c.width, h: c.height};
}
const videoMeta = file => new Promise(res => { const v = document.createElement("video"); v.preload = "metadata"; v.onloadedmetadata = () => { res({w: v.videoWidth, h: v.videoHeight, dur: v.duration}); URL.revokeObjectURL(v.src); }; v.onerror = () => res({}); v.src = URL.createObjectURL(file); });
const memberOf = uid => crewState.members.find(m => m.uid === uid) || {};
function avatarHtml(uid, name){
  const m = memberOf(uid), photo = m.photo || (uid === (crewFS() || {}).uid ? profile().photo : "");
  return photo ? `<img alt="" referrerpolicy="no-referrer" src="${esc(photo)}">` : esc((name || m.name || "?").trim().charAt(0).toUpperCase());
}
/** Text with @mentions of crew members highlighted and links made tappable. */
function richText(el, text){
  const handles = new Set(crewState.members.map(m => (m.handle || "").toLowerCase()).filter(Boolean)); if (myHandle()) handles.add(myHandle());
  const re = /(@[a-z0-9_]{3,20})|(https?:\/\/[^\s<]+)/gi; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) el.appendChild(document.createTextNode(text.slice(last, m.index)));
    if (m[1] && handles.has(m[1].slice(1).toLowerCase())) { const s = document.createElement("span"); s.className = "mention" + (m[1].slice(1).toLowerCase() === myHandle() ? " mine" : ""); s.textContent = m[1]; el.appendChild(s); }
    else if (m[2]) { const a = document.createElement("a"); a.className = "lnk"; a.href = m[2]; a.target = "_blank"; a.rel = "noopener"; a.textContent = m[2]; el.appendChild(a); }
    else el.appendChild(document.createTextNode(m[0]));
    last = m.index + m[0].length;
  }
  if (last < text.length) el.appendChild(document.createTextNode(text.slice(last)));
}
const mediaUrl = key => "/api/media/" + key;

function openChat(){
  const fs = crewFS(); if (!fs || !chat.code) return;
  chat.open = true; markChatSeen();
  const el = document.createElement("div"); el.className = "chatv"; el.id = "chatv";
  el.innerHTML = `<div class="ch"><button class="back" aria-label="Back">←</button>${CHAT_ICON}<div><b></b><small></small></div></div>
    <div class="cl" role="log" aria-live="polite"></div>
    <div class="cc"><div class="replybar" hidden></div><div class="mentions" hidden></div><div class="needhandle" hidden></div>
      <div class="crow"><button class="ib att" aria-label="Attach">${CI.clip}</button><textarea rows="1" maxlength="1000" placeholder="Message" aria-label="Message"></textarea><button class="snd" aria-label="Hold to record a voice note">${CI.mic}</button></div>
      <div class="rec" hidden><span class="dotr"></span><span class="rt">0:00</span><span class="hint">‹ Slide to cancel</span></div></div>`;
  el.querySelector(".ch b").textContent = crewState.name || "Crew";
  const names = crewState.members.map(m => m.handle ? "@" + m.handle : firstName(m.name));
  el.querySelector(".ch small").textContent = `${crewState.members.length} member${crewState.members.length === 1 ? "" : "s"}${names.length ? " · " + names.slice(0, 4).join(", ") : ""}`;
  document.body.appendChild(el);
  history.pushState({chat: 1}, "");
  window.addEventListener("popstate", closeChatBack);
  el.querySelector(".back").onclick = () => history.back();
  wireComposer(el);
  drawReply(); drawNeedHandle();
  drawChat(true);
}
function closeChatBack(){
  chat.open = false; window.removeEventListener("popstate", closeChatBack);
  if (vn.audio) vn.audio.pause();
  const el = $("chatv"); if (el) el.remove(); renderCrew();
}
function drawNeedHandle(){
  const el = $("chatv"); if (!el) return;
  const box = el.querySelector(".needhandle"), row = el.querySelector(".crow");
  if (myHandle()) { box.hidden = true; row.hidden = false; return; }
  box.hidden = false; row.hidden = true;
  box.innerHTML = `<input maxlength="20" autocapitalize="off" spellcheck="false" placeholder="@${esc(suggestHandle())}"><button class="btn primary">Save</button><p>Pick your @handle to chat. It's how your crew mentions you.</p>`;
  const inp = box.querySelector("input"); inp.value = suggestHandle();
  inp.oninput = () => { inp.value = inp.value.toLowerCase().replace(/[^a-z0-9_]/g, ""); };
  box.querySelector("button").onclick = async () => { try { await claimHandle(inp.value); drawNeedHandle(); drawChat(true); } catch(e) { box.querySelector("p").textContent = e.message; } };
}
function drawReply(){
  const el = $("chatv"); if (!el) return;
  const b = el.querySelector(".replybar");
  if (!chat.reply) { b.hidden = true; return; }
  b.hidden = false; b.innerHTML = `<i></i><div><b></b><span></span></div><button aria-label="Cancel reply">✕</button>`;
  b.querySelector("b").textContent = "Reply to " + chat.reply.name; b.querySelector("span").textContent = chat.reply.text;
  b.querySelector("button").onclick = () => { chat.reply = null; drawReply(); };
}
function wireComposer(el){
  const ta = el.querySelector("textarea"), snd = el.querySelector(".snd"), men = el.querySelector(".mentions");
  const mode = () => { const typing = !!ta.value.trim(); snd.innerHTML = typing ? CI.send : CI.mic; snd.setAttribute("aria-label", typing ? "Send" : "Hold to record a voice note"); snd.dataset.mode = typing ? "send" : "mic"; };
  const grow = () => { ta.style.height = "44px"; ta.style.height = Math.min(140, ta.scrollHeight) + "px"; mode(); mentionPick(); };
  ta.oninput = grow; mode();
  const send = () => { const t = ta.value.trim(); if (!t) return; postMessage({text: t}); ta.value = ""; grow(); ta.focus(); };
  ta.onkeydown = e => { if (e.key === "Enter" && !e.shiftKey && !("ontouchstart" in window)) { e.preventDefault(); send(); } };
  // @mention suggestions
  function mentionPick(){
    const pre = ta.value.slice(0, ta.selectionStart), m = /(^|\s)@([a-z0-9_]*)$/i.exec(pre);
    if (!m) { men.hidden = true; return; }
    const q = m[2].toLowerCase();
    const list = crewState.members.filter(x => x.uid !== (crewFS() || {}).uid && x.handle && (x.handle.startsWith(q) || (x.name || "").toLowerCase().startsWith(q))).slice(0, 6);
    if (!list.length) { men.hidden = true; return; }
    men.hidden = false; men.innerHTML = "";
    list.forEach(x => { const b = document.createElement("button"); b.innerHTML = `<span class="av">${avatarHtml(x.uid, x.name)}</span><span><b></b><small></small></span>`;
      b.querySelector("b").textContent = x.name || ""; b.querySelector("small").textContent = "@" + x.handle;
      b.onmousedown = e => e.preventDefault();
      b.onclick = () => { const start = pre.length - m[2].length - 1; ta.value = ta.value.slice(0, start) + "@" + x.handle + " " + ta.value.slice(ta.selectionStart); ta.focus(); const c = start + x.handle.length + 2; ta.setSelectionRange(c, c); men.hidden = true; mode(); };
      men.appendChild(b); });
  }
  ta.onclick = mentionPick;
  // send, or hold to record
  let startX = 0, holdT = null;
  snd.onpointerdown = e => {
    if (snd.dataset.mode === "send") return;
    e.preventDefault(); startX = e.clientX; snd.setPointerCapture(e.pointerId);
    holdT = setTimeout(() => { holdT = null; startRec(el); }, 180);
  };
  snd.onpointermove = e => { if (vn.rec && e.clientX - startX < -90) stopRec(el, false); };
  const up = () => {
    if (holdT) { clearTimeout(holdT); holdT = null; toast("Hold the mic to record, release to send."); return; }
    if (vn.rec) stopRec(el, true);
  };
  snd.onpointerup = up; snd.onpointercancel = () => { if (holdT) { clearTimeout(holdT); holdT = null; } if (vn.rec) stopRec(el, false); };
  snd.onclick = () => { if (snd.dataset.mode === "send") send(); };
  el.querySelector(".att").onclick = () => attachSheet(el);
}
function sheet(el, items){
  const sh = document.createElement("div"); sh.className = "csheet";
  sh.innerHTML = `<div class="card"></div>`;
  items.forEach(([icon, label, fn, cls]) => { const b = document.createElement("button"); if (cls) b.className = cls; b.innerHTML = `${icon}<span></span>`; b.lastChild.textContent = label; b.onclick = () => { sh.remove(); fn(); }; sh.firstChild.appendChild(b); });
  sh.onclick = e => { if (e.target === sh) sh.remove(); };
  el.appendChild(sh);
}
function attachSheet(el){
  const pick = (accept, capture) => { const i = document.createElement("input"); i.type = "file"; i.accept = accept; if (capture) i.capture = capture; else i.multiple = true; i.onchange = () => i.files.length && previewSend(el, [...i.files]); i.click(); };
  sheet(el, [[CI.photo, "Photo or video", () => pick("image/*,video/*")], [CI.camera, "Take a photo", () => pick("image/*", "environment")], [CI.video, "Record a video", () => pick("video/*", "environment")]]);
}
/** Telegram-style preview with a caption before sending. */
function previewSend(el, files){
  files = files.filter(f => /^(image|video)\//.test(f.type));
  if (!files.length) return toast("Photos and videos only.");
  const big = files.find(f => f.type.startsWith("video/") && f.size > 25 * 1024 * 1024);
  if (big) return toast("Videos up to 25 MB (about 1–2 minutes). Trim it and try again.");
  const pv = document.createElement("div"); pv.className = "cprev";
  pv.innerHTML = `<div class="pt"><button aria-label="Cancel">✕</button><span>${files.length > 1 ? files.length + " items" : files[0].type.startsWith("video/") ? "Video" : "Photo"}</span><span></span></div>
    <div class="pm"></div><div class="pb"><input maxlength="1000" placeholder="Add a caption…"><button aria-label="Send">${CI.send}</button></div>`;
  const f0 = files[0], url = URL.createObjectURL(f0), pm = pv.querySelector(".pm");
  pm.innerHTML = f0.type.startsWith("video/") ? `<video src="${url}" controls playsinline></video>` : `<img alt="" src="${url}">`;
  if (files.length > 1) pm.insertAdjacentHTML("beforeend", `<div class="many">+ ${files.length - 1} more</div>`);
  pv.querySelector(".pt button").onclick = () => { URL.revokeObjectURL(url); pv.remove(); };
  pv.querySelector(".pb button").onclick = async () => {
    const cap = pv.querySelector("input").value; URL.revokeObjectURL(url); pv.remove();
    for (let i = 0; i < files.length; i++) {
      const f = files[i], c = i === 0 ? cap : "";
      if (f.type.startsWith("video/")) { const meta = await videoMeta(f); sendMedia(f, "video", {w: meta.w || 0, h: meta.h || 0, dur: meta.dur || 0}, c); }
      else { try { const {blob, w, h} = await prepImage(f); sendMedia(blob, "image", {w, h}, c); } catch(e) { toast("Couldn't read that photo."); } }
    }
  };
  el.appendChild(pv);
  pv.querySelector("input").focus();
}
// ---- voice notes
const vn = {rec: null, stream: null, chunks: [], t0: 0, levels: [], timer: null, ctx: null, audio: null, playing: null};
async function startRec(el){
  if (!navigator.mediaDevices || !window.MediaRecorder) return toast("Voice notes aren't supported here.");
  try { vn.stream = await navigator.mediaDevices.getUserMedia({audio: {echoCancellation: true, noiseSuppression: true}}); }
  catch(e) { return toast("ORDO needs the microphone for voice notes. Allow it in your phone's settings."); }
  const mime = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4", "audio/webm"].find(t => MediaRecorder.isTypeSupported(t)) || "";
  vn.rec = new MediaRecorder(vn.stream, mime ? {mimeType: mime, audioBitsPerSecond: 32000} : undefined);
  vn.chunks = []; vn.levels = []; vn.t0 = Date.now();
  vn.rec.ondataavailable = e => e.data.size && vn.chunks.push(e.data);
  vn.rec.start(250);
  try {
    vn.ctx = new (window.AudioContext || window.webkitAudioContext)();
    const an = vn.ctx.createAnalyser(); an.fftSize = 512; vn.ctx.createMediaStreamSource(vn.stream).connect(an);
    const buf = new Uint8Array(an.fftSize);
    vn.sample = setInterval(() => { an.getByteTimeDomainData(buf); let s = 0; for (const v of buf) s += (v - 128) ** 2; vn.levels.push(Math.sqrt(s / buf.length)); }, 70);
  } catch(e){}
  const snd = el.querySelector(".snd"), rec = el.querySelector(".rec"), row = el.querySelector(".crow");
  snd.classList.add("rec"); rec.hidden = false; row.querySelector("textarea").style.visibility = "hidden"; row.querySelector(".att").style.visibility = "hidden";
  const rt = rec.querySelector(".rt");
  vn.timer = setInterval(() => { const s = (Date.now() - vn.t0) / 1000; rt.textContent = fmtSec(Math.floor(s)); if (s >= 300) stopRec(el, true); }, 200);
  try { navigator.vibrate && navigator.vibrate(30); } catch(e){}
}
function stopRec(el, send){
  const r = vn.rec; if (!r) return;
  vn.rec = null; clearInterval(vn.timer); clearInterval(vn.sample);
  const dur = (Date.now() - vn.t0) / 1000, levels = vn.levels.slice();
  r.onstop = () => {
    vn.stream.getTracks().forEach(t => t.stop()); try { vn.ctx && vn.ctx.close(); } catch(e){}
    if (!send) { toast("Voice note discarded."); return; }
    if (dur < 0.8) { toast("Hold the mic a little longer."); return; }
    const blob = new Blob(vn.chunks, {type: (r.mimeType || "audio/webm").split(";")[0]});
    const N = 40, wave = []; for (let i = 0; i < N; i++) { const a = levels.slice(Math.floor(i * levels.length / N), Math.floor((i + 1) * levels.length / N)); wave.push(a.length ? Math.max(...a) : 0); }
    const mx = Math.max(1, ...wave);
    sendMedia(blob, "audio", {dur: Math.round(dur * 10) / 10, wave: wave.map(v => Math.round(v / mx * 31))}, "");
  };
  r.stop();
  const snd = el.querySelector(".snd"), rec = el.querySelector(".rec"), row = el.querySelector(".crow");
  snd.classList.remove("rec"); rec.hidden = true; row.querySelector("textarea").style.visibility = ""; row.querySelector(".att").style.visibility = "";
}
function voiceBubble(m, src){
  const w = document.createElement("div"); w.className = "vn";
  const wave = (m.media && m.media.wave) || Array.from({length: 40}, (_, i) => 8 + (i * 7) % 20);
  w.innerHTML = `<button class="vp" aria-label="Play">${CI.play}</button><div class="vw">${wave.map(v => `<i style="height:${Math.max(3, v / 31 * 26)}px"></i>`).join("")}</div><span class="vt">${fmtSec(Math.round((m.media && m.media.dur) || 0))}</span>`;
  const btn = w.querySelector(".vp"), bars = [...w.querySelectorAll(".vw i")], vt = w.querySelector(".vt"), total = (m.media && m.media.dur) || 0;
  const paint = (t, playing) => { const k = total ? t / total : 0; bars.forEach((b, i) => b.classList.toggle("on", i / bars.length < k)); vt.textContent = playing ? fmtSec(Math.floor(t)) + " / " + fmtSec(Math.round(total)) : fmtSec(Math.round(total)); btn.innerHTML = playing ? CI.pause : CI.play; };
  btn.onclick = () => {
    if (!vn.audio) vn.audio = new Audio();
    const a = vn.audio;
    if (vn.playing === w && !a.paused) { a.pause(); return; }
    if (vn.playing !== w) { if (vn.playing && vn.playing.__paint) vn.playing.__paint(0, false); a.src = src; vn.playing = w; }
    a.ontimeupdate = () => paint(a.currentTime, true); a.onpause = () => paint(a.currentTime, false); a.onended = () => { paint(0, false); vn.playing = null; };
    a.play().catch(() => toast("Couldn't play that voice note."));
  };
  w.__paint = paint;
  return w;
}
function viewImage(el, src){
  const v = document.createElement("div"); v.className = "cview";
  v.innerHTML = `<div class="pt"><button>✕ Close</button><button>${"Save to phone"}</button></div><img alt="">`;
  v.querySelector("img").src = src;
  const [cl, sv] = v.querySelectorAll("button");
  cl.onclick = () => v.remove();
  sv.onclick = async () => { try { const b = await (await fetch(src)).blob(); const r = new FileReader(); r.onload = () => saveToDevice(r.result, `ORDO-chat-${Date.now()}.jpg`) && toast("Saved to your phone."); r.readAsDataURL(b); } catch(e) { toast("Couldn't save it."); } };
  el.appendChild(v);
}
function msgMenu(el, it, me){
  const fs = crewFS(), items = [[CI.reply, "Reply", () => { chat.reply = {id: it.id, name: firstName(it.name), text: msgPreview(it).slice(0, 120)}; drawReply(); el.querySelector("textarea").focus(); }]];
  if (it.text) items.push([CI.copy, "Copy text", () => { navigator.clipboard && navigator.clipboard.writeText(it.text).then(() => toast("Copied.")).catch(() => {}); }]);
  if (it.media && it.media.type === "image") items.push([CI.save, "Save photo", () => viewImage(el, mediaUrl(it.media.key))]);
  if (me) items.push([CI.del, "Delete for everyone", () => {
    fs.db.collection("groups").doc(chat.code).collection("messages").doc(it.id).delete().catch(e => toast("Couldn't delete: " + e.message));
    if (it.media && it.media.key) fs.user.getIdToken().then(t => fetch(mediaUrl(it.media.key), {method: "DELETE", headers: {authorization: "Bearer " + t}})).catch(() => {});
  }, "danger"]);
  sheet(el, items);
}
function drawChat(stick){
  const el = $("chatv"), fs = crewFS(); if (!el || !fs) return;
  const cl = el.querySelector(".cl"), atBottom = cl.scrollHeight - cl.scrollTop - cl.clientHeight < 120;
  const items = [...chat.msgs.map(m => ({...m, kind: "msg"})), ...feedState.events.map(e => ({...e, kind: "event"})),
    ...chat.pending.map(p => ({id: p.pid, pid: p.pid, uid: fs.uid, name: profile().name, text: p.text, ts: p.ts, kind: "msg", pending: p, media: {type: p.kind, ...p.extra}}))].sort((a, b) => a.ts - b.ts);
  const playingSrc = vn.playing && vn.audio && !vn.audio.paused ? vn.audio.src : null;
  cl.innerHTML = "";
  if (!items.length) { cl.innerHTML = `<div class="empty">${CHAT_ICON.replace('class="cico"', 'class="cico" style="width:64px;height:64px"')}<div>No messages yet. Say something to your crew: a plan, a win, a call-out. Hold the mic for a voice note.</div></div>`; return; }
  const today = keyOf(new Date()), yest = shift(today, -1);
  let lastDay = null, prev = null;
  items.forEach(it => {
    const d = keyOf(new Date(it.ts));
    if (d !== lastDay) { lastDay = d; prev = null; const s = document.createElement("div"); s.className = "dsep"; s.textContent = d === today ? "Today" : d === yest ? "Yesterday" : fromKey(d).toLocaleDateString(undefined, {weekday: "long", day: "numeric", month: "long"}); cl.appendChild(s); }
    if (it.kind === "event") {
      const s = document.createElement("div"); s.className = "sysl"; s.innerHTML = "<b></b> <span></span>";
      s.querySelector("b").textContent = it.uid === fs.uid ? "You" : it.name; s.querySelector("span").textContent = it.text;
      cl.appendChild(s); prev = null; return;
    }
    const me = it.uid === fs.uid, cont = prev && prev.uid === it.uid && it.ts - prev.ts < 5 * 60000;
    const m = document.createElement("div"); m.className = "msg" + (me ? " me" : "") + (cont ? " cont" : ""); m.id = "m-" + it.id;
    if (it.pid) m.dataset.pid = it.pid;
    m.innerHTML = `<span class="av">${avatarHtml(it.uid, it.name)}</span><div class="bb"></div>`;
    const bb = m.querySelector(".bb");
    if (!me) { const nm = document.createElement("div"); nm.className = "nm"; nm.textContent = it.name || "Member"; if (it.handle) { const h = document.createElement("small"); h.textContent = "@" + it.handle; nm.appendChild(h); } bb.appendChild(nm); }
    if (it.replyTo) {
      const q = document.createElement("span"); q.className = "rq"; q.innerHTML = "<b></b><span></span>";
      q.querySelector("b").textContent = it.replyTo.name; q.querySelector("span").textContent = it.replyTo.text;
      q.onclick = e => { e.stopPropagation(); const t = $("m-" + it.replyTo.id); if (t) { t.scrollIntoView({block: "center", behavior: "smooth"}); t.classList.add("flash"); setTimeout(() => t.classList.remove("flash"), 1200); } };
      bb.appendChild(q);
    }
    if (it.media) {
      const src = it.pending ? it.pending.local : mediaUrl(it.media.key);
      if (it.media.type === "audio") bb.appendChild(voiceBubble(it, src));
      else {
        const box = document.createElement("div"); box.className = "media";
        if (it.media.type === "image") {
          const im = document.createElement("img"); im.alt = "Photo"; im.loading = "lazy"; im.src = src;
          if (it.media.w && it.media.h) im.style.aspectRatio = `${it.media.w} / ${it.media.h}`;
          im.onclick = e => { e.stopPropagation(); if (!it.pending) viewImage(el, src); };
          box.appendChild(im);
        } else {
          const v = document.createElement("video"); v.src = src; v.controls = true; v.playsInline = true; v.preload = "metadata";
          if (it.media.w && it.media.h) v.style.aspectRatio = `${it.media.w} / ${it.media.h}`;
          box.appendChild(v);
        }
        if (it.pending) { const u = document.createElement("div"); u.className = "up" + (it.pending.error ? " err" : ""); u.textContent = it.pending.error ? it.pending.error + " Tap to dismiss." : Math.round(it.pending.progress * 100) + "%"; if (it.pending.error) u.onclick = () => { chat.pending = chat.pending.filter(x => x !== it.pending); drawChat(false); }; box.appendChild(u); }
        bb.appendChild(box);
      }
      if (it.pending && it.media.type === "audio") { const u = document.createElement("div"); u.className = "vt"; u.style.fontFamily = "var(--f-mono)"; u.style.fontSize = "11px"; u.textContent = it.pending.error ? it.pending.error : "Sending…"; bb.appendChild(u); }
    }
    const tx = document.createElement("span"); tx.className = "tx"; richText(tx, it.text || ""); bb.appendChild(tx);
    const tm = document.createElement("time"); tm.textContent = new Date(it.ts).toLocaleTimeString(undefined, {hour: "2-digit", minute: "2-digit"}); bb.appendChild(tm);
    if (!it.pending) {
      let lp = null;
      bb.oncontextmenu = e => { e.preventDefault(); msgMenu(el, it, me); };
      bb.onpointerdown = e => { if (e.target.closest("button,video,a,.rq")) return; lp = setTimeout(() => { lp = null; try { navigator.vibrate && navigator.vibrate(15); } catch(_){} msgMenu(el, it, me); }, 450); };
      bb.onpointerup = bb.onpointerleave = bb.onpointercancel = () => { if (lp) { clearTimeout(lp); lp = null; } };
    }
    cl.appendChild(m); prev = it;
    if (playingSrc && it.media && it.media.type === "audio" && playingSrc.endsWith(mediaUrl(it.media.key))) { const w = m.querySelector(".vn"); vn.playing = w; }
  });
  if (stick || atBottom) cl.scrollTop = cl.scrollHeight;
}

''' + s[j:]
open(P, "w", encoding="utf-8", newline="\n").write(s)

# ---- service worker: keep chat media on the phone after the first view
SW = os.path.join(ROOT, "sw.js"); w = open(SW, encoding="utf-8").read()
a = '''  if (same && url.pathname.startsWith("/api/")) return;              // reminder / crew server: always live'''
assert a in w
w = w.replace(a, '''  if (same && url.pathname.startsWith("/api/media/")) {               // chat photos, videos, voice notes: download once
    e.respondWith((async () => {
      const c = await caches.open(MEDIA_CACHE), hit = await c.match(url.pathname);
      if (hit) return hit;
      if (req.headers.has("range")) { e.waitUntil(fetch(url.pathname).then(r => r.ok && c.put(url.pathname, r)).catch(() => {})); return fetch(req); }
      const res = await fetch(req); if (res.ok) c.put(url.pathname, res.clone()); return res;
    })());
    return;
  }
  if (same && url.pathname.startsWith("/api/")) return;              // reminder / crew server: always live''')
w = w.replace('const CACHE = "ordo-v2";', 'const CACHE = "ordo-v3", MEDIA_CACHE = "ordo-media";')
w = w.replace("for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);", "for (const k of await caches.keys()) if (k !== CACHE && k !== MEDIA_CACHE) await caches.delete(k);")
open(SW, "w", encoding="utf-8", newline="\n").write(w)

# ---- rules: media messages + handles
R = os.path.join(ROOT, "firestore.rules"); r = open(R, encoding="utf-8").read()
a = '''        allow create: if request.auth != null && isMember() && request.resource.data.uid == request.auth.uid
          && request.resource.data.text is string && request.resource.data.text.size() > 0 && request.resource.data.text.size() <= 1000;'''
assert a in r
r = r.replace(a, '''        allow create: if request.auth != null && isMember() && request.resource.data.uid == request.auth.uid
          && request.resource.data.get('text', '') is string && request.resource.data.get('text', '').size() <= 1000
          && (request.resource.data.get('text', '').size() > 0 || request.resource.data.get('media', null) is map);''')
a = '''    // Crews: anyone signed in'''
r = r.replace(a, '''    // @handles: one owner each; anyone signed in can check whether one is taken.
    match /handles/{h} {
      allow read: if request.auth != null;
      allow create: if request.auth != null && request.resource.data.uid == request.auth.uid && h.matches('^[a-z0-9_]{3,20}$');
      allow update: if request.auth != null && resource.data.uid == request.auth.uid && request.resource.data.uid == request.auth.uid;
      allow delete: if request.auth != null && resource.data.uid == request.auth.uid;
    }

    // Crews: anyone signed in''', 1)
open(R, "w", encoding="utf-8", newline="\n").write(r)
print("ok")
