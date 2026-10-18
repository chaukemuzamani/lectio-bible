import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import speech,structure,insert_en,audit_quotes
from lib import load
sp,_=speech.build();S=structure.bsb_structure();K=load("KJVS");out={}
n=0
for b in K:
    verses=[((b,ci+1,vi+1),v) for ci,ch in enumerate(K[b]) for vi,v in enumerate(ch)]
    plan=insert_en.plan_book(verses,sp,lambda r:[r])
    res=insert_en.realize(plan,lambda vi:S.get(verses[vi][0],{}).get("p",False))
    out[b]=[];i=0
    for ci,ch in enumerate(K[b]):
        out[b].append(res[i:i+len(ch)]);i+=len(ch)
    n+=sum(1 for r in res for t in r if isinstance(t,dict) and t.get("a"))
print("marks inserted",n)
audit_quotes.audit(out)
import pickle;pickle.dump(out,open("/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/kjvq.pkl","wb"))
