"""Insert quotation marks into English versions that print none."""
import sys,os,pickle,time;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import speech,structure,insert_en,audit_quotes,sources
from vrs import to_kjv,PROT
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
VC={"DRA":"vul","Brenton":"lxx"}
_sp=None;_S=None
def ctx():
    global _sp,_S
    if _sp is None: _sp,_=speech.build();_S=structure.bsb_structure()
    return _sp,_S
def run(code,base=None,vs=None):
    sp,S=ctx()
    vs=vs if vs is not None else {}
    vcf=lambda b:vs.get(b,VC.get(code,"kjv"))
    K=base or sources.load_base(code)
    def refs_of(r):
        if r[0] not in PROT: return []
        return to_kjv(vcf(r[0]),*r)
    out={};n=0
    for b in K:
        verses=[((b,ci+1,vi+1),sources.as_tokens(v)) for ci,ch in enumerate(K[b]) for vi,v in enumerate(ch)]
        if b not in PROT:
            out[b]=K[b];continue
        plan=insert_en.plan_book(verses,sp,refs_of,snap_red=(code=="KJVS"))
        def para(vi):
            ks=refs_of(verses[vi][0])
            return bool(ks) and S.get(ks[0],{}).get("p",False)
        res=insert_en.realize(plan,para)
        out[b]=[];i=0
        for ci,ch in enumerate(K[b]):
            out[b].append(res[i:i+len(ch)]);i+=len(ch)
        n+=sum(1 for r in res for t in r if isinstance(t,dict) and t.get("a"))
    print(code,"marks inserted",n)
    if __name__=="__main__":
        audit_quotes.audit(out,limit=4)
        pickle.dump(out,open(Q+code+".pkl","wb"))
    return out
if __name__=="__main__":
    for c in sys.argv[1:]:
        t=time.time();run(c);print("  ",round(time.time()-t),"s")
