"""One-off: the share sheet lets you pick the exact app (each WhatsApp separately) for reports, stakes and crew invites."""
import os
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")
s = open(P, encoding="utf-8").read()

def rep(a, b):
    global s
    assert s.count(a) == 1, f"{s.count(a)} matches: " + a[:90]
    s = s.replace(a, b)

rep("</style>\n</head>", r""".sheet .apps .ic img{width:100%;height:100%;display:block;border-radius:inherit;object-fit:cover}
.sheet .apps .ic.app{background:transparent!important;padding:0;overflow:hidden}
.sheet .apps .last .ic{box-shadow:0 0 0 2px var(--accent)}
.sheet .apps .last span:last-child::after{content:"Last used";display:block;font-family:var(--f-mono);font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-top:2px}
.sheet .sh-more{justify-self:center}
</style>
</head>""")

i = s.index("function openShare(k){"); j = s.index("function reportButton(k){")
s = s[:i] + r'''const WA_PKGS = ["com.whatsapp", "com.whatsapp.w4b"];
const SHARE_LAST = "ordo-share-last";
/**
 * Pick the exact app to send with. In the ORDO app this lists every app on the phone that can send text,
 * with its own icon, so WhatsApp and WhatsApp Business are separate choices. On the website it offers the
 * phone's own share menu plus direct links.
 * o: {title, text, waText?, smsText?, subject?, phone?, preview?}
 */
function shareSheet(o){
  const phone = (o.phone || "").replace(/[^0-9]/g, ""), waText = o.waText || o.text, smsText = o.smsText || o.text;
  const sh = document.createElement("div"); sh.className = "sheet";
  sh.innerHTML = `<div class="card" role="dialog" aria-label="${esc(o.title)}">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h3></h3><button class="btn" data-x>Close</button></div>
    ${o.preview === false ? "" : "<pre></pre>"}
    <div class="fl">Send with</div><div class="apps"></div>
    <p class="beat" id="shareNote"></p></div>`;
  sh.querySelector("h3").textContent = o.title;
  if (o.preview !== false) sh.querySelector("pre").textContent = o.text;
  const apps = sh.querySelector(".apps"), note = sh.querySelector("#shareNote");
  const close = () => sh.remove();
  const tile = (label, iconHtml, onclick, cls) => {
    const el = document.createElement("button"); if (cls) el.className = cls;
    el.innerHTML = `${iconHtml}<span></span>`; el.lastChild.textContent = label;
    el.onclick = onclick; apps.appendChild(el); return el;
  };
  const svgIc = (color, icon) => `<span class="ic" style="background:${color}">${SHARE_ICONS[icon]}</span>`;
  const copy = () => tile("Copy", svgIc("#111318", "copy"), async () => {
    try { await navigator.clipboard.writeText(o.text); note.textContent = "Copied. Paste it anywhere."; }
    catch(e) { const pre = sh.querySelector("pre"); if (pre) { const r = document.createRange(); r.selectNodeContents(pre); getSelection().removeAllRanges(); getSelection().addRange(r); } note.textContent = "Selected. Copy it from your keyboard menu."; }
  });
  let T = [];
  if (NATIVE && NATIVE.shareTargets) { try { T = JSON.parse(NATIVE.shareTargets()); } catch(e){} }
  if (T.length) {
    let last = null; try { last = localStorage.getItem(SHARE_LAST); } catch(e){}
    const pri = p => p === last ? 0 : WA_PKGS.includes(p) ? 1 + WA_PKGS.indexOf(p) : p === "org.telegram.messenger" ? 3 : /sms|messag|mms/i.test(p) ? 4 : /mail|gm$/i.test(p) ? 5 : 9;
    T.sort((a, b) => pri(a.pkg) - pri(b.pkg) || a.label.localeCompare(b.label));
    const FIRST = 8, render = all => {
      apps.innerHTML = "";
      (all ? T : T.slice(0, FIRST)).forEach(t => tile(t.label, `<span class="ic app"><img alt="" src="${t.icon}"></span>`, () => {
        try { localStorage.setItem(SHARE_LAST, t.pkg); } catch(e){}
        NATIVE.shareTo(t.pkg, WA_PKGS.includes(t.pkg) ? waText : t.pkg === "org.telegram.messenger" ? o.text : (/sms|messag|mms/i.test(t.pkg) ? smsText : o.text), phone);
        close();
      }, t.pkg === last ? "last" : ""));
      copy();
      if (!all && T.length > FIRST) { const m = document.createElement("button"); m.className = "linkbtn sh-more"; m.textContent = `Show all ${T.length} apps`; m.onclick = () => { m.remove(); render(true); }; apps.after(m); }
    };
    render(false);
    if (phone && T.some(t => WA_PKGS.includes(t.pkg))) note.textContent = `WhatsApp opens your partner's chat (+${phone}). Pick the WhatsApp you use for them.`;
  } else {
    if (navigator.share || (NATIVE && NATIVE.share)) tile("Choose app", svgIc("#7C8BFF", "more"), () => {
      if (NATIVE && NATIVE.share) NATIVE.share(o.text, o.subject || o.title); else navigator.share({text: o.text}).catch(() => {});
    });
    const link = (label, color, icon, href) => { const a = document.createElement("a"); a.href = href; a.target = "_blank"; a.rel = "noopener"; a.innerHTML = `${svgIc(color, icon)}<span>${label}</span>`; apps.appendChild(a); };
    link("WhatsApp", "#25D366", "wa", `https://api.whatsapp.com/send?${phone ? "phone=" + phone + "&" : ""}text=${encodeURIComponent(waText)}`);
    link("Telegram", "#2AABEE", "tg", `https://t.me/share/url?url=${encodeURIComponent(location.origin + location.pathname)}&text=${encodeURIComponent(o.text)}`);
    link("SMS", "#4B5563", "sms", `sms:${phone ? "+" + phone : ""}?body=${encodeURIComponent(smsText)}`);
    link("Email", "#3B4CE0", "mail", `mailto:?subject=${encodeURIComponent(o.subject || o.title)}&body=${encodeURIComponent(o.text)}`);
    copy();
    if (navigator.share) note.textContent = "Two WhatsApps on this phone? Tap Choose app to pick the right one.";
  }
  sh.onclick = e => { if (e.target === sh || e.target.hasAttribute("data-x")) close(); };
  document.body.appendChild(sh);
}
function openShare(k){
  shareSheet({title: "Send your report", text: reportText(k, "plain"), waText: reportText(k, "wa"), smsText: reportText(k, "sms"),
    subject: "ORDO day report · " + fromKey(k).toLocaleDateString(undefined, {weekday: "short", day: "numeric", month: "short"}), phone: acct().partner || ""});
}
''' + s[j:]

rep('''  const inv = document.createElement("a"); inv.className = "linkbtn"; inv.target = "_blank"; inv.rel = "noopener";
  inv.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(`Join my crew on ORDO for ${(settings.challenge || {}).name || "our challenge"}.\\n\\n1. Open ${location.origin}${location.pathname}\\n2. Sign in with Google\\n3. Crew → Join → code ${code}`)}`;
  inv.textContent = "Invite on WhatsApp";''', '''  const inv = document.createElement("button"); inv.className = "linkbtn";
  const invText = `Join my crew on ORDO for ${(settings.challenge || {}).name || "our challenge"}.\\n\\n1. Open ${location.origin}${location.pathname}\\n2. Sign in with Google\\n3. Crew → Join → code ${code}`;
  inv.onclick = () => shareSheet({title: "Invite to your crew", text: invText, subject: "Join my crew on ORDO"});
  inv.textContent = "Invite friends";''')
open(P, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
