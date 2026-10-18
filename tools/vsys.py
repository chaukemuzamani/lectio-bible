"""Per-book versification of each version, and the tables the reader uses to line verses up."""
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from vrs import V,PROT,USFM,to_kjv
SYSTEMS=["kjv","org","rso","lxx","vul"]
def maxv(sysname,u):
    return V("eng" if sysname=="kjv" else sysname).maxv.get(u)
def detect(books):
    """{book: system} for the books whose chapter/verse layout fits another system better than the KJV's."""
    out={}
    for b,chs in books.items():
        if b not in PROT: continue
        u=USFM[PROT.index(b)]
        counts=[len(ch) for ch in chs]
        # trailing empty verses do not count
        best=None
        for s in SYSTEMS:
            mv=maxv(s,u)
            if not mv: continue
            sc=sum(1 for i,n in enumerate(counts) if i<len(mv) and mv[i]==n)-2*abs(len(mv)-len(counts))
            key=(sc,-SYSTEMS.index(s))
            if best is None or key>best[0]: best=(key,s)
        if best and best[1]!="kjv": out[b]=best[1]
    return out
def table(sysname,books_counts):
    """native -> canonical refs where they differ: {book: {"c:v": [[c,v],...]}}"""
    out={}
    for b,counts in books_counts.items():
        d={}
        for c,n in enumerate(counts,1):
            for v in range(1,n+1):
                ks=[k for k in to_kjv(sysname,b,c,v) if k[0]==b]
                if ks!=[(b,c,v)]: d[f"{c}:{v}"]=[[k[1],k[2]] for k in ks]
        if d: out[b]=d
    return out
