"""Rebuild every version's data file with quotation marks, red letters, psalm titles, headings
and paragraphs.

    python3 build_data.py [CODE ...]      (no codes: all versions)
"""
import sys,os,json,re,time,pickle,copy,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sources,titles,run_en,run_ru,normalize,redletter,headings,vsys,speech
from lib import DATA,load
from vrs import PROT,to_kjv
SCR="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data")

EN_OWN=["BSB","WEB","WEBY","LSV","FBV","OEB","WMB"]
EN_INS=["KJVS","ASV","Darby","Webster","UKJV","Geneva","DRA","Tyndale","BBE","Brenton"]
EN_NORM=["YLT","JPS","NHEBME"]
RU_INS=["RusSynodal","CSlElizabeth","RusMakarij"]
OTHER=["Shona"]
GREEK=["GRK","SBLT","TR","BYZ"]
ALL=EN_OWN+EN_INS+EN_NORM+RU_INS+OTHER+GREEK+["HEB"]
FIXED={"DRA":"vul","Brenton":"lxx","RusSynodal":"rso","CSlElizabeth":"rso","JPS":"org"}
LANG={c:"ru" for c in RU_INS};LANG.update({"Shona":"sn"})

_sp=None;_reds=None
def sp():
    global _sp
    if _sp is None: _sp,_=speech.build()
    return _sp
def reds():
    global _reds
    if _reds is None: _reds=redletter.red_pids(sp())
    return _reds

def versification(code,B):
    if code in FIXED: return {b:FIXED[code] for b in B if b in PROT}
    if code=="RusMakarij": return {}
    return vsys.detect(B)

def depth_fn(vs):
    S=sp()
    def f(b,c,v):
        ks=to_kjv(vs.get(b,"kjv"),b,c,v)
        return S[ks[0]]["depth"] if ks and ks[0] in S else 0
    return f

def strip_book_markers(B):
    """JPS prints “BOOK I” … at the start of a psalm verse; that belongs in a heading."""
    P=B.get("Psalms")
    if not P: return
    for ch in P:
        if ch and ch[0] and isinstance(ch[0][0],str):
            ch[0][0]=re.sub(r"^\s*BOOK (I|II|III|IV|V)\s+","",ch[0][0])

def cleanup(v):
    """Final token list for one verse."""
    out=[];seen_text=False
    for t in v:
        if isinstance(t,dict):
            if "q" in t: t={"q":t["q"]}
            elif "l" in t and "h" not in t:
                if seen_text: t=" "
                else: continue
            elif t.get("p") and seen_text: t=" "
            elif t.get("br") and not seen_text and not out: continue
        if isinstance(t,str):
            if not t: continue
            if t==" " and out and isinstance(out[-1],str) and out[-1].endswith(" "): continue
            if out and isinstance(out[-1],str):
                s=out[-1]+t
                out[-1]=re.sub(r"  +"," ",s);continue
            if t.strip(): seen_text=True
        elif isinstance(t,list): seen_text=True
        elif isinstance(t,dict) and "q" in t: seen_text=True
        out.append(t)
    # trailing / leading spaces
    while out and isinstance(out[-1],str) and not out[-1].strip(): out.pop()
    if out and isinstance(out[-1],str): out[-1]=out[-1].rstrip()
    i=0
    while i<len(out) and isinstance(out[i],dict) and ("h" in out[i] or out[i].get("p")): i+=1
    if i<len(out) and isinstance(out[i],str): out[i]=out[i].lstrip()
    out=[t for t in out if not (isinstance(t,str) and t=="")]
    if len(out)==1 and isinstance(out[0],str): return out[0]
    if not out: return ""
    return out

def old_title(code):
    p=f"{DATA}/{code}"
    if os.path.isdir(p): return json.load(open(p+"/index.json"))
    return {"t":json.load(open(p+".json"))["t"]}

def write(code,books,order):
    p=f"{OUT}/{code}"
    if os.path.isdir(p):
        ix=json.load(open(p+"/index.json"))
        for name,nch,i in ix["b"]:
            json.dump({"c":books[name]},open(f"{p}/{i}.json","w"),ensure_ascii=False,separators=(",",":"))
    else:
        t=json.load(open(p+".json"))["t"]
        d={"t":t,"b":[{"n":n,"c":books[n]} for n in order]}
        json.dump(d,open(p+".json","w"),ensure_ascii=False,separators=(",",":"))

def build(code):
    t0=time.time();lang=LANG.get(code,"en")
    if code in GREEK or code=="HEB":
        B={b:[[sources.as_tokens(v) if isinstance(v,(list,str)) else v for v in ch] for ch in chs] for b,chs in load(code).items()}
        order=list(B)
        if code in GREEK:
            B={b:[[[([t[0].replace("¶","").strip()]+list(t[1:])) if isinstance(t,list) else t for t in v] for v in ch] for ch in chs] for b,chs in B.items()}
            B=redletter.greek_red(B)
        B={b:[[cleanup(v) if isinstance(v,list) else v for v in ch] for ch in chs] for b,chs in B.items()}
        write(code,B,order);return code,round(time.time()-t0),{}
    B=sources.load_base(code)
    order=list(load(code).keys())
    for b in list(B):
        if b not in order: order.append(b)
    vs=versification(code,B)
    stats={}
    if code=="JPS": strip_book_markers(B)
    # psalm titles
    if code not in ("BSB","WEBY","WEB","WMB"):
        stats["titles"]=titles.mark(B,vs.get("Psalms","kjv"),"ru" if lang=="ru" else "en")
    # quotation marks
    if code in EN_INS:
        B=run_en.run(code,base=B,vs=vs)
    elif code in RU_INS:
        B=run_ru.run(code,base=B,vs=vs)
    elif code in EN_NORM:
        normalize.normalize_books(code,B,depth_fn(vs))
    stats["marks"]=sum(1 for b in B for ch in B[b] for v in ch for t in v if isinstance(t,dict) and "q" in t)
    # red letters
    if code in EN_INS and code!="KJVS" or code in RU_INS:
        B=redletter.apply_pids(B,reds())
    elif code in ("BSB","WEB","LSV","FBV","OEB","WMB","YLT","NHEBME"):
        B=redletter.own_quote_red(B,code,"en",lambda b:vs.get(b,"kjv"))
    elif code=="Shona":
        B=redletter.own_quote_red(B,code,"sn",lambda b:vs.get(b,"kjv"))
    stats["red"]=sum(1 for b in B for ch in B[b] for v in ch for t in sources.as_tokens(v) if isinstance(t,dict) and t.get("r")==1)
    # headings and paragraphs
    if code=="BSB": headings.convert_bsb(B)
    else:
        B={b:[[sources.as_tokens(v) for v in ch] for ch in chs] for b,chs in B.items()}
        stats["headings"]=headings.add(B,lang,lambda b:vs.get(b,"kjv"),paragraphs=(code!="WEBY"))
    B={b:[[cleanup(sources.as_tokens(v)) for v in ch] for ch in chs] for b,chs in B.items()}
    write(code,B,order)
    pickle.dump(vs,open(SCR+f"vs_{code}.pkl","wb"))
    return code,round(time.time()-t0),stats

def write_vrs():
    """data/vrs.json: per-version book versification and native -> KJV verse tables."""
    sysmap={};used=set()
    for code in ALL:
        p=SCR+f"vs_{code}.pkl"
        if os.path.exists(p):
            vs=pickle.load(open(p,"rb"))
            if vs: sysmap[code]=vs;used|=set(vs.values())
    tables={}
    for s in sorted(used):
        counts={}
        for code,vs in sysmap.items():
            D=load(code)
            for b,sy in vs.items():
                if sy==s and b in D:
                    n=[len(ch) for ch in D[b]]
                    if b not in counts or len(n)>len(counts[b]) or sum(n)>sum(counts[b]): counts[b]=n
        # include the full layout of the system for those books (max verses from the .vrs)
        from vrs import USFM
        for b in list(counts):
            mv=vsys.maxv(s,USFM[PROT.index(b)])
            if mv: counts[b]=[max(a,b2) for a,b2 in zip(mv+[0]*(len(counts[b])-len(mv)),counts[b]+[0]*(len(mv)-len(counts[b])))]
        tables[s]=vsys.table(s,counts)
    json.dump({"ver":sysmap,"map":tables},open(f"{OUT}/vrs.json","w"),ensure_ascii=False,separators=(",",":"))
    return {k:len(v) for k,v in tables.items()}

if __name__=="__main__":
    codes=sys.argv[1:] or ALL
    for c in codes:
        if c=="vrs": print(write_vrs());continue
        print(build(c),flush=True)
