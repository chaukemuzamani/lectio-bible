"""Verses where the BSB prints speech marks but a version with inserted marks has no quotation there."""
import sys,pickle,collections;sys.path.insert(0,'.')
import sources,quotes,wstruct
from vrs import PROT
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
code=sys.argv[1];K=pickle.load(open(Q+code+".pkl","rb"));B=sources.bsbu()
def inside(chs):
    res={}
    for ci,ch in enumerate(chs):
        for vi,v in enumerate(ch): pass
    return res
miss=[];tot=0
for b in PROT:
    if b not in K: continue
    d=0;st=[]
    for ci,ch in enumerate(B[b]):
        for vi,toks in enumerate(ch):
            text,br,_=wstruct.flat(toks);start=len(st);ev,st=quotes.scan(text,st,br)
            bsb_speech=start>0 or any(e[1] in "oc" for e in ev)
            try: kv=K[b][ci][vi]
            except IndexError: continue
            has=any(isinstance(t,dict) and "q" in t for t in kv)
            kd=d
            for t in kv:
                if isinstance(t,dict) and "q" in t and not t.get("ro"):
                    d+= 1 if t["q"] in "“‘" else -1
            if bsb_speech:
                tot+=1
                if not has and kd==0: miss.append((b,ci+1,vi+1))
print(code,"BSB speech verses",tot,"missing in",code,len(miss))
import collections
print(collections.Counter(m[0] for m in miss).most_common(20))
import random;random.seed(1)
for m in random.sample(miss,min(25,len(miss))): print(m)
