// Lectio service worker — build 202610191913
const SHELL="lectio-shell-202610191913",DATA="lectio-data",FONTS="lectio-fonts";
const SHELL_FILES=["./","index.html","manifest.webmanifest","icons/icon-192.png","icons/icon-512.png","icons/apple-touch-icon.png","icons/favicon-32.png","data/morph.json","data/vrs.json"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(SHELL).then(c=>c.addAll(SHELL_FILES)).then(()=>self.skipWaiting()))});
// On update: drop old app shells, and refresh only the saved Bible files whose contents changed
async function refreshData(){
  try{
    const nh=await (await fetch("data/hashes.json",{cache:"no-store"})).json();
    const c=await caches.open(DATA);const prev=await c.match("__hashes");
    if(!prev){for(const k of await c.keys())await c.delete(k)}
    else{const oh=await prev.json();for(const [f,h] of Object.entries(oh))if(nh[f]!==h)await c.delete(f)}
    await c.put("__hashes",new Response(JSON.stringify(nh),{headers:{"Content-Type":"application/json"}}));
  }catch(e){}
}
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith("lectio-shell-")&&k!==SHELL).map(k=>caches.delete(k)))).then(refreshData).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request;if(r.method!=="GET")return;
  const u=new URL(r.url);
  if(u.origin==="https://fonts.googleapis.com"||u.origin==="https://fonts.gstatic.com"){
    e.respondWith(caches.open(FONTS).then(async c=>{const hit=await c.match(r);const net=fetch(r).then(res=>{if(res.ok)c.put(r,res.clone());return res}).catch(()=>hit);return hit||net}));return}
  if(u.origin!==location.origin)return;
  if(u.pathname.includes("/versions/")&&!u.pathname.includes("/data/")){
    // earlier versions: from the network, kept for offline use, never mixed with the current app
    e.respondWith(caches.open("lectio-versions").then(async c=>{try{const res=await fetch(r);if(res.ok)c.put(r,res.clone());return res}catch(err){return (await c.match(r,{ignoreSearch:true}))||Response.error()}}));return}
  if(r.mode==="navigate"||u.pathname.endsWith("/index.html")){
    e.respondWith(fetch(r).then(res=>{caches.open(SHELL).then(c=>c.put("index.html",res.clone()));return res}).catch(()=>caches.match("index.html")));return}
  if(u.pathname.includes("/data/")){
    // Bible data: from the device when saved, otherwise download and keep it
    e.respondWith(caches.open(DATA).then(async c=>{const hit=await c.match(r,{ignoreSearch:true});if(hit)return hit;const res=await fetch(r);if(res.ok)c.put(r,res.clone());return res}));return}
  e.respondWith(caches.match(r).then(hit=>hit||fetch(r)));
});
