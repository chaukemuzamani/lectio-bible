import sys,os,json;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import speech,structure,insert_en,sources
from lib import load,vt
sp,_=speech.build();S=structure.bsb_structure()
K=load("KJVS")
def show(book,chs):
    verses=[((book,ci+1,vi+1),v) for ci,ch in enumerate(K[book]) for vi,v in enumerate(ch)]
    plan=insert_en.plan_book(verses,sp,lambda r:[r])
    res=insert_en.realize(plan,lambda vi:S.get(verses[vi][0],{}).get("p",False))
    for (ref,_),toks in zip(verses,res):
        if ref[1] in chs:
            s=""
            for t in toks:
                if isinstance(t,str): s+=t
                elif isinstance(t,list): s+=t[0]
                elif isinstance(t,dict) and "q" in t: s+=t["q"]
                elif isinstance(t,dict) and t.get("r")==1: s+="⟦"
                elif isinstance(t,dict) and t.get("r")==0: s+="⟧"
            print(f"{ref[1]}:{ref[2]} {s}")
for b,c in [(a.split(":")[0],[int(x) for x in a.split(":")[1].split(",")]) for a in sys.argv[1:]]: show(b,c)
