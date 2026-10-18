"""Checks on the finished data files."""
import sys,os,json,re,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
D="/home/claude/lectio-bible/data"
def load(code):
    p=f"{D}/{code}"
    if os.path.isdir(p):
        ix=json.load(open(p+"/index.json"));return {n:json.load(open(f"{p}/{i}.json"))["c"] for n,c,i in ix["b"]}
    return {b["n"]:b["c"] for b in json.load(open(p+".json"))["b"]}
def text_of(v,red=True):
    if isinstance(v,str): return v
    s=""
    for t in v:
        if isinstance(t,str): s+=t
        elif isinstance(t,list): s+=(" " if len(t)>=6 and s and not s.endswith(" ") else "")+t[0]
        elif isinstance(t,dict):
            if "q" in t: s+=t["q"]
            elif t.get("r")==1 and red: s+="⟦"
            elif t.get("r")==0 and red: s+="⟧"
    return s
RU={"RusSynodal","CSlElizabeth","RusMakarij"}
def audit(code):
    B=load(code);P=collections.Counter();ex=collections.defaultdict(list)
    for b,chs in B.items():
        depth=0
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                ref=f"{b} {ci+1}:{vi+1}"
                if isinstance(v,str): continue
                # red balance
                r=[t.get("r") for t in v if isinstance(t,dict) and "r" in t]
                st=0
                for x in r:
                    if x==1:
                        if st: P["red nested"]+=1;ex["red nested"].append(ref)
                        st=1
                    else:
                        if not st: P["red close w/o open"]+=1;ex["red close w/o open"].append(ref)
                        st=0
                if st: P["red open at end"]+=1;ex["red open at end"].append(ref)
                s=text_of(v)
                # narrator words inside red before the first quotation mark
                for m in re.finditer(r"⟦([^⟧]*)",s):
                    seg=m.group(1)
                    first=re.search(r"[“‘«„]",seg)
                    pre=seg[:first.start()] if first else seg
                    if re.search(r"\b(said|saith|answered|сказал|говорит|отвечал|рече|глагола)\b",pre) and first:
                        P["narrator in red"]+=1;ex["narrator in red"].append(ref+" "+seg[:80])
                # inserted quotation marks per book
                for t in v:
                    if isinstance(t,dict) and "q" in t:
                        q=t["q"]
                        if code in RU: op= q in "«„"
                        else: op= q in "“‘"
                        depth+= 1 if op else -1
                        if depth<0: P["close w/o open"]+=1;ex["close w/o open"].append(ref);depth=0
                # headings
                for t in v:
                    if isinstance(t,dict) and "h" in t: P["headings"]+=1
                    if isinstance(t,dict) and t.get("d")==1: P["titles"]+=1
                    if isinstance(t,dict) and "q" in t: P["marks"]+=1
                    if isinstance(t,dict) and t.get("r")==1: P["red spans"]+=1
                    if isinstance(t,dict) and t.get("p"): P["paragraphs"]+=1
        if depth>0: P["unclosed at book end"]+=1;ex["unclosed at book end"].append(b)
    return P,ex
if __name__=="__main__":
    for c in sys.argv[1:]:
        P,ex=audit(c);print(c,dict(P))
        for k,v in ex.items(): print("    ",k,v[:4])
