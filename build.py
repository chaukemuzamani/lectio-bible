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
      let urls=["data/morph.json","data/lex-heb.json","data/lex-grk.json"];
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
  window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferred=e;$("#instRow").hidden=false});
  $("#instBtn").onclick=async()=>{if(!deferred)return;deferred.prompt();await deferred.userChoice.catch(()=>{});deferred=null;$("#instRow").hidden=true};
  const ios=/iphone|ipad|ipod/i.test(navigator.userAgent),standalone=window.matchMedia("(display-mode: standalone)").matches||navigator.standalone;
  if(ios&&!standalone){$("#instRow").hidden=false;$("#instBtn").hidden=true;$("#instNote").textContent="In Safari, tap Share, then “Add to Home Screen”"}
}''')
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
const SHELL_FILES=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/apple-touch-icon.png","icons/favicon-32.png","data/morph.json"];
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
