import sys;sys.path.insert(0,'.')
import sources
from vrs import PROT
K=sources.load_base("KJVS")
def diff(code):
    D=sources.load_base(code);out=[]
    for b in PROT:
        if b not in D: continue
        kc=[len(c) for c in K[b]];dc=[len([v for v in c]) for c in D[b]]
        # treat trailing empty verses
        if kc!=dc:
            d=[(i+1,kc[i] if i<len(kc) else None,dc[i] if i<len(dc) else None) for i in range(max(len(kc),len(dc))) if (kc[i] if i<len(kc) else None)!=(dc[i] if i<len(dc) else None)]
            out.append((b,d[:4],len(d)))
    return out
for c in sys.argv[1:]:
    r=diff(c);print(c,len(r),"books differ");[print("   ",x) for x in r[:12]]
