"""Section headings and paragraph starts from the BSB, keyed by canonical (KJV-numbered) verse."""
import re
import sources
from vrs import PROT
BOOKRE=None
def parse_refs(x):
    """'(Matthew 5:3–12; Luke 6:20–23)' -> [["Matthew",5,3,12],["Luke",6,20,23]]"""
    out=[];book=None
    names=sorted(set(PROT)|{"Psalm","1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","1 Corinthians","2 Corinthians","1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","1 Peter","2 Peter","1 John","2 John","3 John","Revelation","Song of Songs"},key=len,reverse=True)
    alias={"Psalm":"Psalms","1 Samuel":"I Samuel","2 Samuel":"II Samuel","1 Kings":"I Kings","2 Kings":"II Kings","1 Chronicles":"I Chronicles","2 Chronicles":"II Chronicles","1 Corinthians":"I Corinthians","2 Corinthians":"II Corinthians","1 Thessalonians":"I Thessalonians","2 Thessalonians":"II Thessalonians","1 Timothy":"I Timothy","2 Timothy":"II Timothy","1 Peter":"I Peter","2 Peter":"II Peter","1 John":"I John","2 John":"II John","3 John":"III John","Revelation":"Revelation of John","Song of Songs":"Song of Solomon"}
    for part in re.split(r"[;,]\s*(?=[1-3]?\s?[A-Z]|\d)",x.strip("() ")):
        part=part.strip()
        m=None
        for n in names:
            if part.startswith(n+" "): m=n;break
        if m: book=alias.get(m,m);part=part[len(m):].strip()
        if not book: continue
        mm=re.match(r"(\d+)(?::(\d+))?(?:[–-](\d+)(?::(\d+))?)?",part)
        if not mm: continue
        c=int(mm.group(1))
        if mm.group(2):
            v=int(mm.group(2))
            if mm.group(4): c2,v2=int(mm.group(3)),int(mm.group(4))
            elif mm.group(3): c2,v2=c,int(mm.group(3))
            else: c2,v2=c,v
        else:
            v=1;c2=int(mm.group(3)) if mm.group(3) else c;v2=0      # whole chapter(s)
        out.append([book,c,v,c2,v2])
    return out
def bsb_structure():
    """{(book,c,v): {"h":[heading dicts], "p":bool}} for verse-start structure in the BSB."""
    B=sources.bsbu();S={}
    for b,chs in B.items():
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                hs=[];p=False
                for t in v:
                    if isinstance(t,str) and t.strip(): break
                    if isinstance(t,dict):
                        if "h" in t:
                            h=dict(t)
                            if "x" in h and h.get("l")!=0: h["xr"]=parse_refs(h["x"])
                            hs.append(h);p=True
                        elif t.get("p"): p=True
                        elif t.get("d")==1: break
                if vi==0: p=True
                if hs or p: S[(b,ci+1,vi+1)]={"h":hs,"p":p}
    return S
