"""Accuracy of carried-over quotes on the KJV, measured against the KJV's own red-letter spans."""
import sys,json,re,collections;sys.path.insert(0,".")
import usfx,quotes,wstruct,align_en
from lib import load,get
from vrs import PROT
OB="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/dl/ob/"
S=usfx.parse(OB+("eng-web.usfx.xml" if sys.argv[1]=="WEB" else "eng-bsb.usfx.xml"))
snap=len(sys.argv)<3 or sys.argv[2]!="nosnap"
K=load("KJVS")
def kjv_red_gaps(toks):
    text="";gaps=[];red=False;words_before=0
    flat,_,spans=wstruct.flat(toks)
    tw=align_en.words(flat)
    # offsets of r markers
    pos=0;res=[]
    off=0
    for i,t in enumerate(toks):
        if isinstance(t,dict) and "r" in t:
            # offset = end of text so far
            o=sum(len(x[0]) if isinstance(x,list) else len(x) for x in toks[:i] if isinstance(x,(str,list)))
            res.append((o,"o" if t["r"]==1 else "c"))
    return flat,tw,[(align_en.gap_of(tw,o),k) for o,k in res]
c=collections.Counter();bad=[]
for b in PROT[39:]:
    ss=[]
    for ci,ch in enumerate(S[b]):
        for vi,toks in enumerate(ch):
            kv=get(K,b,ci+1,vi+1)
            stext,sbr,_=wstruct.flat(toks);sev,ss=quotes.scan(stext,ss,sbr)
            if not kv: continue
            ktext,tw,red=kjv_red_gaps(kv)
            # only red boundaries strictly inside the verse are speech boundaries
            red=[(g,k) for g,k in red if 0<g<len(tw)]
            if not red: continue
            ev=[e for e in sev if e[1] in "oc"]
            pred,ratio,_=align_en.transfer(stext,ev,ktext,snap)
            pset=set((g,k) for g,k,l in pred)
            for r in red:
                c["red"]+=1
                if r in pset: c["hit"]+=1
                elif any(abs(g-r[0])<=1 and k==r[1] for g,k in pset): c["near"]+=1
                else:
                    c["miss"]+=1
                    if len(bad)<15: bad.append((b,ci+1,vi+1,r,sorted(pset),ktext[:150]))
print(sys.argv[1:],dict(c),"exact %.1f%%"%(100*c["hit"]/c["red"]),"within1 %.1f%%"%(100*(c["hit"]+c["near"])/c["red"]))
for x in bad: print(x)
