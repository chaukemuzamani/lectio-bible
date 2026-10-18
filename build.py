"""Builds the installable Lectio site from the artifact page (../bible/index.html)."""
import os,re,shutil,json,hashlib,time
SRC="/home/claude/bible";OUT=os.path.dirname(os.path.abspath(__file__))
s=open(f"{SRC}/index.html",encoding="utf-8").read()
def rep(a,b):
    global s
    assert s.count(a)==1,(s.count(a),a[:70]); s=s.replace(a,b)
# --- standalone-only additions ---
rep('''    <div class="set-row"><span>Highlights</span>''','''    <div class="set-row" id="offRow" hidden><span>Offline reading<br><small class="muted" id="offNote">Save the selected version on this device</small></span><button id="offBtn" style="background:none;border:1px solid var(--rule);border-radius:6px;padding:6px 12px;cursor:pointer">Save offline</button></div>
    <div class="set-row" id="instRow" hidden><span>Install app<br><small class="muted" id="instNote">Add Lectio to your home screen or desktop</small></span><button id="instBtn" style="background:none;border:1px solid var(--rule);border-radius:6px;padding:6px 12px;cursor:pointer">Install</button></div>
    <div class="set-row"><span>Highlights</span>''')
rep('''(hlCol?'':'<p class="muted" style="font-size:12px;margin-top:12px">These are saved in this browser. Open the page signed in to keep them in your account.</p>')''','''(hlCol?'':'<p class="muted" style="font-size:12px;margin-top:12px">Highlights are saved on this device.</p>')''')
rep("fillSelects();syncSettings();render();",r'''fillSelects();syncSettings();render();
/* ---------- installable app: offline cache + install ---------- */
if("serviceWorker" in navigator&&(location.protocol==="https:"||location.hostname==="localhost"||location.hostname==="127.0.0.1")){
  navigator.serviceWorker.register("sw.js").catch(()=>{});
  $("#offRow").hidden=false;
  const offUrls=async id=>{
    const vi=vinfo(id),u=[];
    if(vi.dir){const ix=await fetchJSON("data/"+vi.dir+"/index.json");u.push("data/"+vi.dir+"/index.json");ix.b.forEach(([n,c,i])=>u.push("data/"+vi.dir+"/"+i+".json"))}
    else u.push("data/"+id+".json");
    if(!vi.tagged)u.push("data/align/"+id+".json");
    return u;
  };
  $("#offBtn").onclick=async()=>{
    const btn=$("#offBtn");btn.disabled=true;
    try{
      let urls=["data/morph.json","data/lex-heb.json","data/lex-grk.json","data/vrs.json","data/lex/strongs-heb.json","data/lex/strongs-grk.json"];
      for(const id of [S.ver,"HEB","GRK","TR"])urls=urls.concat(await offUrls(id));
      const par=resolvePar();if(par&&!["HEB","GRK","TR"].includes(par))urls=urls.concat(await offUrls(par));
      urls=[...new Set(urls)];let done=0;
      const cache=await caches.open("lectio-data");
      for(let i=0;i<urls.length;i+=6){
        await Promise.all(urls.slice(i,i+6).map(async u=>{if(!(await cache.match(u))){const r=await fetch(u);if(r.ok)await cache.put(u,r)}done++}));
        btn.textContent=Math.round(done/urls.length*100)+"%";
      }
      btn.textContent="Saved ✓";$("#offNote").textContent=vinfo(S.ver).short+(par?" + "+vinfo(par).short:"")+", Hebrew, Greek and word details are on this device";
    }catch(e){btn.textContent="Try again";btn.disabled=false;toast("Could not save everything. Check your connection and try again.")}
  };
  let deferred=null;
  const ua=navigator.userAgent,
    ios=/iphone|ipad|ipod/i.test(ua)||(/Macintosh/.test(ua)&&navigator.maxTouchPoints>1),
    android=/android/i.test(ua),
    standalone=window.matchMedia("(display-mode: standalone)").matches||navigator.standalone===true,
    inApp=/FBAN|FBAV|Instagram|Line\/|Telegram|WhatsApp|Snapchat|MicroMessenger|VKClient|; wv\)/i.test(ua)||(ios&&!/Safari\//.test(ua)),
    samsung=/SamsungBrowser/i.test(ua),firefox=/Firefox|FxiOS/i.test(ua),yandex=/YaBrowser/i.test(ua),
    iosOther=ios&&/CriOS|FxiOS|EdgiOS|OPiOS|YaBrowser/i.test(ua);
  const SHARE='<span class="inst-key"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M10 3v10M6.5 6.5L10 3l3.5 3.5"/><path d="M5 9H4v8h12V9h-1"/></svg>Share</span>',
        DOTS='<span class="inst-key">⋮</span>';
  function instHTML(){
    if(inApp)return '<p style="margin-top:0">This page is open inside another app (such as Telegram or WhatsApp), which can’t install websites.</p><ol class="inst-steps"><li>Tap that app’s menu ('+DOTS+' or <b>…</b>) and choose <b>Open in browser</b>'+(ios?' or <b>Open in Safari</b>':'')+'.</li><li>In '+(ios?'Safari':'Chrome')+', tap <b>Install the app</b> on the home page again.</li></ol><p class="inst-note">Or copy the link and paste it into '+(ios?'Safari':'Chrome')+':</p><button class="inst-copy" id="instCopy">Copy link</button>';
    if(ios)return '<ol class="inst-steps">'+(iosOther?'<li>Tap '+SHARE+' next to the address bar.</li>':'<li>Tap '+SHARE+' at the bottom of Safari (on iPad it’s at the top).</li>')+'<li>Scroll down and tap <b>Add to Home Screen</b>. If it isn’t there, tap <b>Edit Actions…</b> and add it.</li><li>Leave <b>Open as Web App</b> switched on and tap <b>Add</b>.</li></ol><p class="inst-note">Lectio then opens from its icon, full screen, like any other app. '+(iosOther?'If Add to Home Screen is missing, open this page in Safari — other browsers can only do this on iOS 16.4 or later.':'')+'</p>';
    if(android){
      if(samsung)return '<ol class="inst-steps"><li>Tap the menu <span class="inst-key">≡</span> at the bottom right.</li><li>Tap <b>Add page to</b> → <b>Home screen</b>, or <b>Install</b> if it’s offered.</li></ol>';
      if(firefox||yandex)return '<ol class="inst-steps"><li>Tap the menu '+DOTS+'.</li><li>Tap <b>Add to Home screen</b> (or <b>Install</b>).</li></ol><p class="inst-note">If you don’t see it, open this page in Chrome instead.</p>';
      return '<ol class="inst-steps"><li>Tap the menu '+DOTS+' at the top right of Chrome.</li><li>Tap <b>Add to Home screen</b>, then <b>Install</b>. (On some phones the menu says <b>Install app</b>.)</li><li>Confirm, and the Lectio icon appears on your home screen and in your apps.</li></ol><p class="inst-note">If Chrome only offers a shortcut, stay on this page for a few seconds and try again — Chrome checks the app first. Updating Chrome from the Play Store also helps.</p>';
    }
    return '<ol class="inst-steps"><li>In Chrome or Edge, click the install icon at the right end of the address bar, or open the menu '+DOTS+' → <b>Cast, save and share</b> → <b>Install page as app</b>.</li></ol>';
  }
  function hideInst(){$("#homeInst").hidden=true;$("#instRow").hidden=true}
  function showInst(){
    if(deferred){const d=deferred;deferred=null;d.prompt();d.userChoice.then(c=>{if(c&&c.outcome==="accepted")hideInst()}).catch(()=>{});return}
    $("#instBody").innerHTML=instHTML();openSheet("#instSheet");
    const cp=$("#instCopy");if(cp)cp.onclick=async()=>{const u=location.href.split("#")[0];try{await navigator.clipboard.writeText(u);cp.textContent="Copied ✓"}catch(e){prompt("Copy this link:",u)}};
  }
  if(!standalone){$("#homeInst").hidden=false;$("#instRow").hidden=false}
  window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferred=e});
  window.addEventListener("appinstalled",()=>{hideInst();deferred=null;toast("Lectio is installed")});
  $("#homeInst").onclick=showInst;$("#instBtn").onclick=showInst;
}''')
rep('''  <button class="home-last" id="homeLast" hidden>''','''  <button class="home-card home-inst" id="homeInst" hidden>
    <span class="hc-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7.5 10.5L12 15l4.5-4.5"/><path d="M5 19h14"/></svg></span>
    <span class="hc-txt"><span class="hc-t">Install the app</span><span class="hc-m">Open from your home screen, read offline</span></span>
  </button>
  <button class="home-last" id="homeLast" hidden>''')
rep('''<div class="scrim" id="hlSheet" hidden>''','''<div class="scrim" id="instSheet" hidden><div class="sheet" role="dialog" aria-label="Install the app" style="max-width:480px">
  <div class="sheet-head"><h2>Install the app</h2><button class="icon-btn" data-close aria-label="Close">✕</button></div>
  <div class="sheet-body" id="instBody"></div></div></div>
<div class="scrim" id="hlSheet" hidden>''')
rep('''.home-grid{display:grid;''','''.home-inst{margin-top:12px}
.inst-steps{margin:0;padding-left:1.3em;line-height:1.6;font-size:15px}.inst-steps li{margin:8px 0}
.inst-note{font-size:13px;color:var(--ink-soft);margin:14px 0 0;line-height:1.5}
.inst-key{display:inline-flex;align-items:center;gap:4px;border:1px solid var(--rule);border-radius:5px;padding:0 6px;background:var(--leaf);font-weight:500;white-space:nowrap}
.inst-key svg{width:14px;height:14px}
.inst-copy{margin-top:12px;background:var(--rubric);color:var(--leaf);border:none;border-radius:6px;padding:9px 14px;cursor:pointer;font-weight:500}
.home-grid{display:grid;''')
# split into head / body
i=s.index("<header")
head_part,body_part=s[:i],s[i:]
build=time.strftime("%Y%m%d%H%M")
doc=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Read the Bible in many versions side by side, with the Hebrew and Greek, word details, footnotes and highlights.">
<meta name="theme-color" content="#f6f7f4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#15171c" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Lectio">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<style>:root{{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}*,*::before,*::after{{box-sizing:inherit}}body{{margin:0}}img{{max-width:100%}}</style>
{head_part.replace('<meta name="claude:viewport-fit-sides" content="cover">','')}
</head>
<body>
{body_part}
</body>
</html>
'''
open(f"{OUT}/index.html","w",encoding="utf-8").write(doc)
# manifest
json.dump({"name":"Lectio Bible","short_name":"Lectio","description":"Many Bible versions side by side, with Hebrew and Greek word details.",
 "start_url":"./","scope":"./","display":"standalone","background_color":"#f6f7f4","theme_color":"#1d2129",
 "icons":[{"src":"icons/icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icons/icon-512.png","sizes":"512x512","type":"image/png"},
          {"src":"icons/maskable-192.png","sizes":"192x192","type":"image/png","purpose":"maskable"},{"src":"icons/maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]},
 open(f"{OUT}/manifest.webmanifest","w"),indent=1)
# service worker
open(f"{OUT}/sw.js","w").write(f'''// Lectio service worker — build {build}
const SHELL="lectio-shell-{build}",DATA="lectio-data",FONTS="lectio-fonts";
const SHELL_FILES=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/apple-touch-icon.png","icons/favicon-32.png","data/morph.json","data/vrs.json"];
self.addEventListener("install",e=>{{e.waitUntil(caches.open(SHELL).then(c=>c.addAll(SHELL_FILES)).then(()=>self.skipWaiting()))}});
// On update: drop old app shells, and refresh only the saved Bible files whose contents changed
async function refreshData(){{
  try{{
    const nh=await (await fetch("data/hashes.json",{{cache:"no-store"}})).json();
    const c=await caches.open(DATA);const prev=await c.match("__hashes");
    if(!prev){{for(const k of await c.keys())await c.delete(k)}}
    else{{const oh=await prev.json();for(const [f,h] of Object.entries(oh))if(nh[f]!==h)await c.delete(f)}}
    await c.put("__hashes",new Response(JSON.stringify(nh),{{headers:{{"Content-Type":"application/json"}}}}));
  }}catch(e){{}}
}}
self.addEventListener("activate",e=>{{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith("lectio-shell-")&&k!==SHELL).map(k=>caches.delete(k)))).then(refreshData).then(()=>self.clients.claim()))}});
self.addEventListener("fetch",e=>{{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);
  if(u.origin==="https://fonts.googleapis.com"||u.origin==="https://fonts.gstatic.com"){{
    e.respondWith(caches.open(FONTS).then(async c=>{{const hit=await c.match(r);const net=fetch(r).then(res=>{{if(res.ok)c.put(r,res.clone());return res}}).catch(()=>hit);return hit||net}}));return}}
  if(u.origin!==location.origin)return;
  if(r.mode==="navigate"||u.pathname.endsWith("/index.html")){{
    e.respondWith(fetch(r).then(res=>{{caches.open(SHELL).then(c=>c.put("index.html",res.clone()));return res}}).catch(()=>caches.match("index.html")));return}}
  if(u.pathname.includes("/data/")){{
    // Bible data: from the device when saved, otherwise download and keep it
    e.respondWith(caches.open(DATA).then(async c=>{{const hit=await c.match(r,{{ignoreSearch:true}});if(hit)return hit;const res=await fetch(r);if(res.ok)c.put(r,res.clone());return res}}));return}}
  e.respondWith(caches.match(r).then(hit=>hit||fetch(r)));
}});
''')
# data
if os.path.realpath(f"{SRC}/data")!=os.path.realpath(f"{OUT}/data"):     # the page's data folder may be this one
    if os.path.exists(f"{OUT}/data"): shutil.rmtree(f"{OUT}/data")
    shutil.copytree(f"{SRC}/data",f"{OUT}/data",ignore=shutil.ignore_patterns("_*","hashes.json"))
open(f"{OUT}/.nojekyll","w").write("")
hashes={}
for root,_,fs in os.walk(f"{OUT}/data"):
    for f in fs:
        if f=="hashes.json": continue
        full=os.path.join(root,f);rel=os.path.relpath(full,OUT).replace(os.sep,"/")
        hashes[rel]=hashlib.sha1(open(full,"rb").read()).hexdigest()[:12]
json.dump(hashes,open(f"{OUT}/data/hashes.json","w"),separators=(",",":"),sort_keys=True)
print("built",build)
