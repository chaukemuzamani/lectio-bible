"""Base texts for every version, with known source problems repaired.

Each loader returns {book: [[verse, ...], ...]} where a verse is a token list (see usfx.py).
"""
import json,gzip,re,os,difflib,collections
import usfx,osis
from lib import load as load_data,vt,get
from vrs import PROT,USFM
DL="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/dl/"
OB=DL+"ob/";BS=DL+"bs/public/bibles/";SM=DL+"sm/formats/json/"
def as_tokens(v):
    if v is None: return []
    if isinstance(v,str): return [v] if v else []
    return list(v)
def norm_books(d):
    return {b:[[as_tokens(v) for v in ch] for ch in chs] for b,chs in d.items()}
_cache={}
def webu():   # WEB (older revision, Yahweh) with full structure — the speech/red/paragraph source
    if "webu" not in _cache: _cache["webu"]=usfx.parse(OB+"eng-web.usfx.xml")
    return _cache["webu"]
def bsbu():
    if "bsbu" not in _cache:
        d=usfx.parse(OB+"eng-bsb.usfx.xml")
        for b in d:
            for ch in d[b]:
                for v in ch:
                    for i,t in enumerate(v):
                        if isinstance(t,str): v[i]=re.sub(r"\bA Psalms of\b","A Psalm of",t)
        _cache["bsbu"]=d
    return _cache["bsbu"]
def bs(name):
    d=json.load(gzip.open(BS+name+".json.gz"))["books"]
    return {PROT[USFM.index(k)]:[[([x] if x else []) for x in ch] for ch in v] for k,v in d.items() if k in USFM}
def titles_from_webu(sub):
    """Psalm superscriptions from the WEB source, with name substitutions applied."""
    W=webu();out={}
    for ci,ch in enumerate(W["Psalms"]):
        if not ch: continue
        v=ch[0]
        if any(isinstance(t,dict) and t.get("d")==1 for t in v):
            i=[k for k,t in enumerate(v) if isinstance(t,dict) and t.get("d")==1][0]
            j=[k for k,t in enumerate(v) if isinstance(t,dict) and t.get("d")==0][0]
            out[ci+1]=sub(" ".join(t for t in v[i+1:j] if isinstance(t,str)).strip())
    return out
def add_titles(books,titles):
    for c,t in titles.items():
        try: v=books["Psalms"][c-1][0]
        except Exception: continue
        if any(isinstance(x,dict) and x.get("d") is not None for x in v): continue
        books["Psalms"][c-1][0]=[{"d":1},t,{"d":0}]+v
def load_base(code):
    if code=="BSB": return bsbu()
    if code=="WEBY":
        return {b:[[[t for t in v if not (isinstance(t,dict) and "h" in t)] for v in ch] for ch in chs] for b,chs in webu().items()}
    if code=="WEB":
        d=bs("engwebp")
        add_titles(d,titles_from_webu(lambda s:re.sub(r"\bYahweh\b","the LORD",s).replace("the LORD’s","the LORD’s")))
        return d
    if code=="Shona": return bs("sna")
    if code=="Geneva":
        j=json.load(open(SM+"Geneva1599.json"))
        return {b["name"]:[[[v["text"]] if v["text"] else [] for v in c["verses"]] for c in b["chapters"]] for b in j["books"] if b["name"] in PROT}
    if code=="JPS": return jps()
    if code=="WMB": return wmb()
    if code=="OEB": return oeb()
    return norm_books(load_data(code))
def wmb():
    M=norm_books(load_data("WMB"));W=load_base("WEB")
    # learn context-free substitutions WEB -> WMB from overlapping verses
    subs=collections.Counter();tot=collections.Counter()
    tk=lambda s:re.findall(r"[\w’']+|[^\w\s]",s)
    for b in PROT:
        for ci,ch in enumerate(W.get(b,[])):
            for vi,v in enumerate(ch):
                m=get(M,b,ci+1,vi+1)
                if not m or not v: continue
                a=tk(vt(v));c=tk(vt(m))
                for w in set(a): tot[w]+=a.count(w)
                sm=difflib.SequenceMatcher(None,a,c,autojunk=False)
                for op,i1,i2,j1,j2 in sm.get_opcodes():
                    if op=="replace" and i2-i1<=3 and j2-j1<=4: subs[(" ".join(a[i1:i2])," ".join(c[j1:j2]))]+=1
    rules=[]
    for (x,y),n in subs.most_common():
        if n<5: break
        if " " not in x and tot[x] and n/tot[x]>=0.9: rules.append((x,y))
        elif " " in x and n>=10: rules.append((x,y))
    rules.sort(key=lambda r:-len(r[0]))
    def conv(s):
        for x,y in rules: s=re.sub(r"(?<![\w’'])"+re.escape(x)+r"(?![\w’'])",y,s)
        return s
    filled=0
    for b in PROT:
        if b not in W: continue
        M.setdefault(b,[])
        for ci,ch in enumerate(W[b]):
            while len(M[b])<=ci: M[b].append([])
            for vi,v in enumerate(ch):
                while len(M[b][ci])<=vi: M[b][ci].append([])
                if not M[b][ci][vi] and v:
                    M[b][ci][vi]=[conv(t) if isinstance(t,str) else t for t in v if isinstance(t,str)];filled+=1
    add_titles(M,titles_from_webu(lambda s:conv(re.sub(r"\bYahweh\b","the LORD",s))))
    print("  WMB: filled",filled,"verses with",len(rules),"rules")
    return M
def jps():
    j=json.load(open(SM+"JPS.json"));base={b["name"]:[[v["text"] for v in c["verses"]] for c in b["chapters"]] for b in j["books"]}
    E=load_data("JPS")
    def nrm(s): return re.sub(r"^\(\d+-\d+\)\s*","",re.sub(r"\s+"," ",s)).strip()
    def restore(s):
        s=s.replace("--","—").replace("`","'")
        s=re.sub(r"HaShem G-d","the LORD God",s)
        s=re.sub(r"(^|[.?!;:]\s+['\"]?|['\"])HaShem",lambda m:m.group(1)+"The LORD",s)
        s=re.sub(r"\bO HaShem\b","O LORD",s)
        s=re.sub(r"\bHaShem\b","the LORD",s)
        s=s.replace("G-d","God").replace("L-rd","Lord")
        return s
    out={};used=0;rest=0
    for b,chs in base.items():
        out[b]=[]
        for ci,ch in enumerate(chs):
            pool=[]
            for cc in (ci-1,ci,ci+1):
                if b in E and 0<=cc<len(E[b]): pool+=[nrm(vt(x)) for x in E[b][cc]]
            row=[]
            for t in ch:
                best=None
                if pool and t.strip():
                    best=max(pool,key=lambda p:difflib.SequenceMatcher(None,p,restore(t),autojunk=False).quick_ratio())
                    if difflib.SequenceMatcher(None,best,restore(t),autojunk=False).ratio()<0.9: best=None
                if best: row.append([best]);used+=1
                elif t.strip(): row.append([restore(t)]);rest+=1
                else: row.append([])
            out[b].append(row)
    print("  JPS: original wording",used,"restored names",rest)
    return out
def oeb():
    """Newer OEB text (eBible) with the structure of the OSIS edition carried over."""
    return norm_books(load_data("OEB"))
def oeb_osis():
    if "oeb" not in _cache: _cache["oeb"]=osis.parse(OB+"eng-us-oeb.osis.xml")
    return _cache["oeb"]
