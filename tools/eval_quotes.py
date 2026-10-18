import sys,json,re,collections;sys.path.insert(0,".")
import usfx,quotes,wstruct,align_en
from lib import load,get,vt
from vrs import PROT
OB="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/dl/ob/"
src_name=sys.argv[1];tgt_name=sys.argv[2]
S=usfx.parse(OB+("eng-web.usfx.xml" if src_name=="WEB" else "eng-bsb.usfx.xml"))
T=load(tgt_name)
def ylt_events(text,st):
    ev=[]
    for i,ch in enumerate(text):
        if ch=="`": st.append("`");ev.append((i,"o",len(st)-1))
        elif ch=="'" and st and not (i>0 and i+1<len(text) and text[i-1].isalpha() and text[i+1].isalpha()):
            ev.append((i,"c",len(st)-1));st.pop()
    return ev,st
res=collections.Counter();examples=[]
for b in PROT:
    if b not in T: continue
    ss=[];ts=[]
    for ci,ch in enumerate(S[b]):
        for vi,toks in enumerate(ch):
            tv=get(T,b,ci+1,vi+1)
            if tv is None: continue
            stext,sbr,_=wstruct.flat(toks);sev,ss=quotes.scan(stext,ss,sbr)
            ttext=vt(tv)
            if tgt_name=="YLT": tev,ts=ylt_events(ttext,ts)
            else: tev,ts=quotes.scan(ttext,ts,{0})
            tev=[e for e in tev if e[1] in "oc" and e[2]==0]; sev=[e for e in sev if e[1] in "oc" and e[2]==0]
            # strip target quote chars for alignment
            sw=align_en.words(stext);tw=align_en.words(ttext)
            m,ratio=align_en.anchors(sw,tw)
            truth=set((align_en.gap_of(tw,o+ (1 if k=="o" else 0)) if k=="o" else align_en.gap_of(tw,o),k) for o,k,l in tev)
            pred=set()
            for o,k,l in sev:
                g=align_en.gap_of(sw,o+1) if k=="o" else align_en.gap_of(sw,o)
                g=align_en.gap_of(sw,o) if k=="o" else g
                lo,hi=align_en.map_gap(g,m,len(sw),len(tw))
                pred.add((align_en.choose(ttext,tw,lo,hi,k,g/max(len(sw),1)),k))
            for p in pred:
                res["pred"]+=1
                if p in truth: res["hit"]+=1
                elif len(examples)<12 and ratio>0.5: examples.append((b,ci+1,vi+1,p,sorted(truth),ttext[:160]))
            res["truth"]+=len(truth)
print(src_name,"->",tgt_name,dict(res),"precision %.1f%% recall %.1f%%"%(100*res["hit"]/max(res["pred"],1),100*res["hit"]/max(res["truth"],1)))
for e in examples: print(e)
