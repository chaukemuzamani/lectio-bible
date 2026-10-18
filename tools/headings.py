"""Section headings and paragraph starts for every version, from the BSB's, placed by verse mapping.
Russian and Church Slavonic get the headings in Russian (headings_ru.json)."""
import sys,os,json;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import re
import structure,sources
ACROSTIC={"ALEPH","BETH","GIMEL","DALETH","HE","WAW","ZAYIN","HETH","TETH","YODH","KAPH","LAMEDH","MEM","NUN","SAMEKH","AYIN","PE","TZADE","KOPH","RESH","SIN AND SHIN","TAW"}
from vrs import PROT,to_kjv,from_kjv
HERE=os.path.dirname(os.path.abspath(__file__))
_S=None;_RU=None
def S():
    global _S
    if _S is None: _S=structure.bsb_structure()
    return _S
def RU():
    global _RU
    if _RU is None: _RU=json.load(open(os.path.join(HERE,"headings_ru.json"),encoding="utf-8"))
    return _RU
def heading_token(h,lang):
    text=RU().get(h["h"],h["h"]) if lang=="ru" else h["h"]
    tok={"h":text,"l":h.get("l",1)}
    if h.get("xr"): tok["xr"]=h["xr"]
    return tok
def add(books,lang,vs_of,paragraphs=True):
    n=0
    for b,chs in books.items():
        if b not in PROT: continue
        sysb=vs_of(b)
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                ks=[k for k in to_kjv(sysb,b,ci+1,vi+1) if k[0]==b]
                if not ks: continue
                k=ks[0]
                nat=[x for x in from_kjv(sysb,*k) if x[0]==b]
                if nat and nat[0]!=(b,ci+1,vi+1): continue
                st=S().get(k)
                if not st: continue
                vt_=" ".join(t if isinstance(t,str) else (t[0] if isinstance(t,list) else "") for t in sources.as_tokens(v))[:40].upper()
                pre=[heading_token(h,lang) for h in st["h"]
                     if not (h["h"].upper() in ACROSTIC and re.search(r"\b"+re.escape(h["h"].upper().split()[0])+r"\b",vt_))]
                if paragraphs and st["p"] and vi>0: pre.append({"p":1})
                if pre:
                    ch[vi]=pre+sources.as_tokens(v);n+=len(st["h"])
    return n
def convert_bsb(books):
    """The BSB keeps its own headings; turn the printed cross-references into links."""
    for b,chs in books.items():
        for ch in chs:
            for v in ch:
                for i,t in enumerate(v):
                    if isinstance(t,dict) and "h" in t:
                        nt={"h":t["h"],"l":t.get("l",1)}
                        if t.get("x") and t.get("l")!=0:
                            xr=structure.parse_refs(t["x"])
                            if xr: nt["xr"]=xr
                        v[i]=nt
    return books
