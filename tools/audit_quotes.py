"""Scan a version with inserted quotation marks for suspicious placements."""
import sys,os,re,collections;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
def render(toks):
    s=""
    for t in toks:
        if isinstance(t,str): s+=t
        elif isinstance(t,list): s+=(" " if len(t)>=6 and s and not s.endswith(" ") else "")+t[0]
        elif isinstance(t,dict) and "q" in t: s+=t["q"]
        elif isinstance(t,dict) and (t.get("p") or ("l" in t and "h" not in t)) and s and not s.endswith(" "): s+=" "
    return s
CHECKS=[("open before speech verb",re.compile(r"[“‘«„](saying|said|saith|says|answered|сказал|говоря)\b",re.I)),
        ("close after speech intro",re.compile(r"\b(saying|said|saith|unto (him|them|her)),?[”’»“]")),
        ("letter after close",re.compile(r"[”»][A-Za-zА-Яа-я]")),
        ("letter before open",re.compile(r"[A-Za-zА-Яа-я][“«]")),
        ("empty quote",re.compile(r"[“«„]\s*[”»]")),
        ("double open",re.compile(r"“\s*“|«\s*«"))]
def audit(books,limit=6):
    found=collections.defaultdict(list)
    for b,chs in books.items():
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                if isinstance(v,str): continue
                if not any(isinstance(t,dict) and t.get("a") for t in v): continue
                s=render(v)
                for name,rx in CHECKS:
                    for m in rx.finditer(s): found[name].append((b,ci+1,vi+1,s[max(0,m.start()-50):m.end()+30]))
    for name,_ in CHECKS:
        print(f"  {name}: {len(found[name])}")
        for x in found[name][:limit]: print("      ",x)
    return found
