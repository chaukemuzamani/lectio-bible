"""End-to-end check of quote insertion: strip a version's own quotation marks, insert ours, compare."""
import sys,os,re,collections;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sources,run_en,align_en
from audit_quotes import render
from vrs import PROT
OPENS="“‘";CLOSES="”’"
def strip(s):
    s=s.replace("“","").replace("”","").replace("‘","")
    return re.sub(r"’(?![A-Za-z])","",s)
def marks(s):
    """[(word_gap,kind)] for quotation marks in s (apostrophes excluded)."""
    out=[];n=0
    for i,ch in enumerate(s):
        if ch in "“‘": out.append((len(align_en.WORD.findall(s[:i])),"o"))
        elif ch=="”" or (ch=="’" and not (i+1<len(s) and s[i+1].isalpha())): out.append((len(align_en.WORD.findall(s[:i])),"c"))
    return out
code=sys.argv[1];books=sys.argv[2:] or PROT
B=sources.load_base(code)
base={b:[[[strip(t) if isinstance(t,str) else t for t in v] for v in ch] for ch in B[b]] for b in books if b in B}
truth={b:[[marks(render(v)) for v in ch] for ch in B[b]] for b in base}
out=run_en.run(code+"_eval",base=base) if False else None
run_en.Q=run_en.Q
res=run_en.run.__wrapped__(code,base) if hasattr(run_en.run,"__wrapped__") else run_en.run(code,base=base)
C=collections.Counter();ex=collections.defaultdict(list)
for b in base:
    for ci,ch in enumerate(res[b]):
        for vi,v in enumerate(ch):
            p=collections.Counter(marks(render(v)));t=collections.Counter(truth[b][ci][vi])
            hit=sum((p&t).values());C["hit"]+=hit;C["pred"]+=sum(p.values());C["truth"]+=sum(t.values())
            if hit<max(sum(p.values()),sum(t.values())) and len(ex[b])<3: ex[b].append((ci+1,vi+1,render(v)[:200],render(B[b][ci][vi])[:200]))
print(code,dict(C),"precision %.1f%%  recall %.1f%%"%(100*C["hit"]/C["pred"],100*C["hit"]/C["truth"]))
for b in list(ex)[:8]:
    for e in ex[b][:2]: print(b,e[0],e[1],"\n   ours:",e[2],"\n   own: ",e[3])
