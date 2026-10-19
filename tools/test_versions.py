"""Open every earlier version (versions/<commit>/) with today's data in Chromium and keep only those that work.

    python3 test_versions.py        (after build.py)

Checks per version: no script errors; KJV John 1, Synodal Psalm 22 and the Hebrew of Genesis 1 show their verses;
clicking a KJV word fills the word details strip. Writes versions/index.json = {commit: 1, ...} for the ones that pass.
"""
import asyncio,subprocess,time,json,os,sys
from playwright.async_api import async_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8771
CASES=[("KJV",42,1),("RusSynodal",18,22),("HEB",0,1)]
async def check(b,cid):
    ctx=await b.new_context(service_workers="block");pg=await ctx.new_page();errs=[]
    pg.on("pageerror",lambda e: errs.append(str(e)))
    url=f"http://localhost:{PORT}/versions/{cid}/"
    res={}
    for ver,bi,ch in CASES:
        await pg.goto(url+f"#{bi}.{ch}")
        await pg.evaluate(f"()=>{{localStorage.setItem('lectio.ver',JSON.stringify('{ver}'));localStorage.setItem('lectio.par2',JSON.stringify(''));localStorage.removeItem('lectio.defVer')}}")
        await pg.reload();await pg.wait_for_timeout(2500)
        res[ver]=await pg.evaluate("document.querySelectorAll('#page [data-v]').length")
    # word details on a KJV word
    await pg.goto(url+"#42.1");await pg.evaluate("()=>localStorage.setItem('lectio.ver',JSON.stringify('KJV'))");await pg.reload();await pg.wait_for_timeout(2500)
    await pg.evaluate("()=>{const w=document.querySelector('#page .w');if(w)w.click()}");await pg.wait_for_timeout(1500)
    det=(await pg.evaluate("(document.querySelector('#sMain')||{}).textContent||''")).strip()
    await ctx.close()
    ok=not errs and all(n>=5 for n in res.values()) and len(det)>3 and "Point at a word" not in det
    return ok,res,det[:40],errs[:2]
async def main():
    ids=sorted(d for d in os.listdir(f"{ROOT}/versions") if os.path.isdir(f"{ROOT}/versions/{d}"))
    good={}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for cid in ids:
            ok,res,det,errs=await check(b,cid);print(cid,"OK" if ok else "FAIL",res,repr(det),errs,flush=True)
            if ok: good[cid]=1
        await b.close()
    json.dump(good,open(f"{ROOT}/versions/index.json","w"))
    print("usable:",len(good),"of",len(ids))
srv=subprocess.Popen(["python3","-m","http.server",str(PORT),"--directory",ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try: asyncio.run(main())
finally: srv.terminate()
