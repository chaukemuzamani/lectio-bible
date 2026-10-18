import json,os,re
DATA="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/orig/data"   # pristine texts (git HEAD); builds write to ../data
from vrs import PROT,USFM,to_kjv,from_kjv
def load(code):
    p=f"{DATA}/{code}"
    if os.path.isdir(p):
        ix=json.load(open(p+"/index.json"));return {n:json.load(open(f"{p}/{i}.json"))["c"] for n,c,i in ix["b"]}
    d=json.load(open(p+".json"));return {b['n']:b['c'] for b in d['b']}
def vt(v):
    if isinstance(v,str): return v.replace("[","").replace("]","")
    o=""
    for t in v:
        if isinstance(t,str): o+=t
        elif isinstance(t,list): o+=(" " if len(t)>=6 and o and not o.endswith(" ") else "")+t[0]
        elif isinstance(t,dict) and t.get("br"): o+=" "
        elif isinstance(t,dict) and "q" in t: o+=t["q"]
    return o.replace("[","").replace("]","")
def get(D,b,c,v):
    try: return D[b][c-1][v-1]
    except Exception: return None
