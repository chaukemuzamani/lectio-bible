import sys,pickle;sys.path.insert(0,'.')
def render(v):
    s=""
    for t in v:
        if isinstance(t,str): s+=t
        elif isinstance(t,list): s+=(" " if len(t)>=6 and s and not s.endswith(" ") else "")+t[0]
        elif isinstance(t,dict):
            if "q" in t: s+=t["q"]
            elif t.get("r")==1: s+="⟦"
            elif t.get("r")==0: s+="⟧"
            elif t.get("d")==1: s+="⟪"
            elif t.get("d")==0: s+="⟫ "
            elif "h" in t: s+="\n   ## "+t["h"]+(" "+t.get("x","") if t.get("x") else "")+"\n   "
            elif t.get("p"): s+="¶ "
    return s
def show(d,specs):
    for spec in specs:
        b,c,a,z=spec.split(":");c,a,z=int(c),int(a),int(z)
        for v in range(a,z+1):
            try: print(f"{b} {c}:{v}",render(d[b][c-1][v-1]))
            except IndexError: pass
        print()
if __name__=="__main__":
    d=pickle.load(open(sys.argv[1],"rb"));show(d,sys.argv[2:])
