"""One-off: an interrupted voice note (left the chat, ORDO in the background) is kept as a draft, per crew, on the
phone: play it, send it, or delete it. Only 🗑 / slide-to-cancel deletes."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)

rep('''function stopRec(el, send){''', '''/** send: true = send now, false = delete, "draft" = keep it in the chat for later (mic still goes off now). */
function stopRec(el, send){''')
rep('''    if (!send) { toast("Voice note deleted."); return; }
    if (dur < 0.7 || !vn.chunks.length) { toast("Too short. Tap the mic to record, then Send."); return; }
    const blob = new Blob(vn.chunks, {type: (r.mimeType || "audio/webm").split(";")[0]});
    const N = 40, wave = []; for (let i = 0; i < N; i++) { const a = levels.slice(Math.floor(i * levels.length / N), Math.floor((i + 1) * levels.length / N)); wave.push(a.length ? Math.max(...a) : 0); }
    const mx = Math.max(1, ...wave);
    sendMedia(blob, "audio", {dur: Math.round(dur * 10) / 10, wave: wave.map(v => Math.round(v / mx * 31))}, "");''',
'''    if (!send) { toast("Voice note deleted."); return; }
    if (dur < 0.7 || !vn.chunks.length) { if (send === true) toast("Too short. Tap the mic to record, then Send."); return; }
    const blob = new Blob(vn.chunks, {type: (r.mimeType || "audio/webm").split(";")[0]});
    const N = 40, wave = []; for (let i = 0; i < N; i++) { const a = levels.slice(Math.floor(i * levels.length / N), Math.floor((i + 1) * levels.length / N)); wave.push(a.length ? Math.max(...a) : 0); }
    const mx = Math.max(1, ...wave), extra = {dur: Math.round(dur * 10) / 10, wave: wave.map(v => Math.round(v / mx * 31))};
    if (send === "draft") { saveVoiceDraft(code, blob, extra); return; }
    sendMedia(blob, "audio", extra, "");''')
rep('''  const dur = (Date.now() - vn.t0) / 1000, levels = vn.levels.slice(), stream = vn.stream, ctx = vn.ctx;
  recUI(el, "off");''', '''  const dur = (Date.now() - vn.t0) / 1000, levels = vn.levels.slice(), stream = vn.stream, ctx = vn.ctx, code = chat.code;
  recUI(el, "off");''')
rep('''  if (vn.state !== "idle") { if (el && vn.rec) stopRec(el, false); else { vn.state = "idle"; releaseMic(vn.stream, vn.ctx); } if (why) toast(why); }''',
    '''  if (vn.state !== "idle") { if (el && vn.rec) stopRec(el, "draft"); else { vn.state = "idle"; releaseMic(vn.stream, vn.ctx); } if (why) toast(why); }''')
rep('''document.addEventListener("visibilitychange", () => { if (document.hidden) releaseAllMedia(vn.state !== "idle" ? "Recording stopped: ORDO went to the background." : ""); });''',
    '''document.addEventListener("visibilitychange", () => { if (document.hidden) releaseAllMedia(vn.state !== "idle" ? "Mic off. Your voice note is saved as a draft in the chat." : ""); });
// ---- voice note drafts (kept on this phone, one per crew)
async function saveVoiceDraft(code, blob, extra){
  vn.draft = {code, blob, ...extra};
  try { await idb.put("vdraft:" + code, {blob, ...extra}); } catch(e){}
  const el = $("chatv"); if (el && chat.code === code) drawVoiceDraft(el);
}
async function loadVoiceDraft(el){
  if (!vn.draft || vn.draft.code !== chat.code) { try { const v = await idb.get("vdraft:" + chat.code); vn.draft = v && v.blob ? {code: chat.code, ...v} : null; } catch(e) { vn.draft = null; } }
  drawVoiceDraft(el);
}
function clearVoiceDraft(){ const c = vn.draft && vn.draft.code; vn.draft = null; if (c) idb.del("vdraft:" + c).catch(() => {}); }
function drawVoiceDraft(el){
  const bar = el.querySelector(".vdraft"), row = el.querySelector(".crow"), snd = el.querySelector(".snd");
  const d = vn.draft && vn.draft.code === chat.code ? vn.draft : null;
  bar.hidden = !d;
  ["textarea", ".att", ".cam2"].forEach(q => { const x = row.querySelector(q); if (x) x.style.visibility = d ? "hidden" : ""; });
  if (!d) { snd.innerHTML = CI.mic; snd.dataset.mode = "mic"; const ta = row.querySelector("textarea"); if (ta) ta.dispatchEvent(new Event("input")); return; }
  bar.innerHTML = `<button class="rtrash" aria-label="Delete draft">${CI.del}</button><span class="dl">Draft</span>`;
  bar.appendChild(voiceBubble({media: {dur: d.dur, wave: d.wave}}, URL.createObjectURL(d.blob)));
  bar.querySelector(".rtrash").onclick = () => { clearVoiceDraft(); drawVoiceDraft(el); toast("Draft deleted."); };
  snd.innerHTML = CI.send; snd.dataset.mode = "draft"; snd.setAttribute("aria-label", "Send voice note");
}''')
rep('''  snd.onclick = () => {
    if (vn.state === "lock") { if (Date.now() - vn.lockAt > 400) stopRec(el, true); return; }''', '''  snd.onclick = () => {
    if (vn.state === "lock") { if (Date.now() - vn.lockAt > 400) stopRec(el, true); return; }
    if (snd.dataset.mode === "draft" && vn.draft) { const d = vn.draft; clearVoiceDraft(); drawVoiceDraft(el); sendMedia(d.blob, "audio", {dur: d.dur, wave: d.wave}, ""); return; }''')
rep('''    if (snd.dataset.mode === "send" || vn.state === "lock" || vn.state === "starting") return;''',
    '''    if (snd.dataset.mode === "send" || snd.dataset.mode === "draft" || vn.state === "lock" || vn.state === "starting") return;''')
# the textarea's mode() must not overwrite the draft's Send button
rep('''  const mode = () => { const typing = !!ta.value.trim(); cam2.hidden = typing;''', '''  const mode = () => { if (vn.draft && vn.draft.code === chat.code) return; const typing = !!ta.value.trim(); cam2.hidden = typing;''')
rep('''      <div class="rlock" hidden>''', '''      <div class="vdraft" hidden></div>
      <div class="rlock" hidden>''')
rep('''  drawReply(); drawNeedHandle();''', '''  drawReply(); drawNeedHandle(); loadVoiceDraft(el);''')
rep("</style>\n</head>", """.chatv .vdraft{position:absolute;left:8px;right:66px;bottom:calc(env(safe-area-inset-bottom,0px) + 8px);display:grid;grid-template-columns:auto auto minmax(0,1fr);gap:8px;align-items:center;background:#1a1d26;border-radius:22px;padding:2px 12px 2px 4px;min-height:48px}
.chatv .vdraft[hidden]{display:none}
.chatv .vdraft .rtrash{display:grid;width:38px;height:38px;border:0;background:none;color:var(--warn);place-content:center;cursor:pointer}
.chatv .vdraft .rtrash svg{width:21px;height:21px}
.chatv .vdraft .dl{font-family:var(--f-mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.chatv .vdraft .vn{min-width:0}
.chatv .vdraft .vn .vp{width:34px;height:34px}
</style>
</head>""")
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
