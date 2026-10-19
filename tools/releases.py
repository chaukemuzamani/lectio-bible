"""Number the releases in releases.json (oldest = 1.0, then 1.1, …) and write them into the page.

    python3 releases.py

The page (../bible/index.html) carries them between /*RELEASES*/ and /*END RELEASES*/ as
const RELEASES=[{v,date,title,notes,id,site}] newest first; id is the commit whose page is kept
under versions/<id>/ on the installed site (the newest release has none: it is the live page).
"""
import os,json,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE="/home/claude/bible/index.html"
def load():
    R=json.load(open(f"{ROOT}/releases.json",encoding="utf-8"))
    for i,r in enumerate(R): r["v"]=f"1.{i}"
    return R
def js():
    R=load()
    out=[{"v":r["v"],"date":r["date"],"title":r["title"],"notes":r["notes"],"id":r.get("commit"),**({"site":1} if r.get("site") else {})} for r in reversed(R)]
    return "const RELEASES="+json.dumps(out,ensure_ascii=False,separators=(",",":"))+";"
def write():
    s=open(PAGE,encoding="utf-8").read()
    new="/*RELEASES*/"+js()+"/*END RELEASES*/"
    s2,n=re.subn(r"/\*RELEASES\*/.*?/\*END RELEASES\*/",lambda m:new,s,flags=re.S)
    assert n==1,"markers not found"
    open(PAGE,"w",encoding="utf-8").write(s2)
if __name__=="__main__":
    write();print([r["v"]+" "+r["title"] for r in load()])
