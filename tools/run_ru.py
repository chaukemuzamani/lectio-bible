import sys,os,pickle,time;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import insert_ru,sources,structure,audit_quotes
from vrs import to_kjv,PROT
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
VC={"RusSynodal":"rso","CSlElizabeth":"rso","RusMakarij":"kjv"}
def get_kp():
    p=Q+"kp.pkl"
    if os.path.exists(p): return pickle.load(open(p,"rb"))
    sp=pickle.load(open(Q+"../sp.pkl","rb"))
    kp=insert_ru.kjv_plan(sp);pickle.dump(kp,open(p,"wb"));return kp
def run(code,books_only=None,base=None,vs=None):
    KP=get_kp();S=structure.bsb_structure()
    vc=vs if vs is not None else VC[code]
    vcf=lambda b:vc.get(b,"kjv") if isinstance(vc,dict) else vc
    B=base if base is not None else sources.load_base(code)
    if books_only: B={b:B[b] for b in books_only}
    hints=insert_ru.strip_own(B)
    plan=insert_ru.plan_version(code,B,vc,"ru",KP,hints)
    out={}
    for b,chs in B.items():
        if b not in plan: out[b]=chs;continue
        def para(c,v):
            ks=to_kjv(vcf(b),b,c,v);return bool(ks) and S.get(ks[0],{}).get("p",False)
        out[b]=insert_ru.realize(chs,plan[b],para)
    n=sum(1 for b in out for ch in out[b] for v in ch for t in v if isinstance(t,dict) and t.get("a"))
    print(code,"marks",n)
    if __name__=="__main__": pickle.dump(out,open(Q+code+".pkl","wb"))
    return out
if __name__=="__main__":
    for c in sys.argv[1:]:
        t=time.time();run(c);print(round(time.time()-t),"s")
