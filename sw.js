// Lectio service worker — build 202610180145
const SHELL="lectio-shell-202610180145",DATA="lectio-data",FONTS="lectio-fonts";
const SHELL_FILES=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/apple-touch-icon.png","icons/favicon-32.png","data/morph.json"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(SHELL).then(c=>c.addAll(SHELL_FILES)).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith("lectio-shell-")&&k!==SHELL).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);
  if(u.origin==="https://fonts.googleapis.com"||u.origin==="https://fonts.gstatic.com"){
    e.respondWith(caches.open(FONTS).then(async c=>{const hit=await c.match(r);const net=fetch(r).then(res=>{if(res.ok)c.put(r,res.clone());return res}).catch(()=>hit);return hit||net}));return}
  if(u.origin!==location.origin)return;
  if(r.mode==="navigate"||u.pathname.endsWith("/index.html")){
    e.respondWith(fetch(r).then(res=>{caches.open(SHELL).then(c=>c.put("index.html",res.clone()));return res}).catch(()=>caches.match("index.html")));return}
  if(u.pathname.includes("/data/")){
    // Bible data: from the device when saved, otherwise download and keep it
    e.respondWith(caches.open(DATA).then(async c=>{const hit=await c.match(r,{ignoreSearch:true});if(hit)return hit;const res=await fetch(r);if(res.ok)c.put(r,res.clone());return res}));return}
  e.respondWith(caches.match(r).then(hit=>hit||fetch(r)));
});
