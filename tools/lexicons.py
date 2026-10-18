"""Build the extra dictionaries shown under “Full entry”.

    python3 lexicons.py

Writes into ../data/lex/:
  strongs-heb.json, strongs-grk.json   Strong's (Open Scriptures, CC BY-SA)
  bdb/<n>.json                         Brown-Driver-Briggs, unabridged (public domain; digital text by Eliran Wong)
  ml/<n>.json                          Liddell & Scott, Intermediate Greek-English Lexicon (Perseus, CC BY-SA 3.0 US)
Chunk n = Strong's number // CHUNK.  Each chunk is {"H123":[html,...]}.
"""
import os,re,json,csv,unicodedata,collections,html
import xml.etree.ElementTree as ET
from vrs import PROT,to_kjv
import betacode.conv as beta

SCR="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/lex/"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","lex")
CHUNK=100

def dump(obj,path):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    t=json.dumps(obj,ensure_ascii=False,separators=(",",":"))
    t=re.sub(r" ?\ufffd","",t)      # one broken character in the Strong's Hebrew source (H7578)
    open(path,"w",encoding="utf-8").write(t)

def chunked(d,sub):
    groups=collections.defaultdict(dict)
    for k,v in d.items(): groups[int(k[1:])//CHUNK][k]=v
    for n,g in groups.items(): dump(g,f"{OUT}/{sub}/{n}.json")
    return len(groups)

# ---------------------------------------------------------------- Strong's
def strongs():
    out={}
    for f,L in (("greek/strongs-greek-dictionary.js","grk"),("hebrew/strongs-hebrew-dictionary.js","heb")):
        t=open(SCR+"strongs/"+f,encoding="utf-8").read();t=t[t.index("{"):t.rindex("}")+1]
        d=json.loads(t);o={}
        for k,v in d.items():
            key=k[0]+str(int(k[1:]))
            if L=="grk":   # a few Greek entries cite Hebrew words with a G prefix (there is no G number above 5624)
                for f2 in ("derivation","strongs_def","kjv_def"):
                    if v.get(f2): v[f2]=re.sub(r"\bG0*(\d+)\b",lambda m:("H" if int(m.group(1))>5624 else "G")+m.group(1).lstrip("0"),v[f2])
            o[key]=[v.get("lemma",""),v.get("translit") or v.get("xlit",""),v.get("pron",""),
                    (v.get("derivation") or "").strip(),(v.get("strongs_def") or "").strip(),(v.get("kjv_def") or "").strip()]
        if L=="grk": o=greek_xml(o)
        dump(o,f"{OUT}/strongs-{L}.json");out[L]=o
    return out

def greek_xml(fallback):
    """Strong's Greek from the Open Scriptures XML (keeps the Greek words the JS edition drops)."""
    t=open(SCR+"strongs/greek/StrongsGreekDictionaryXML_1.4/strongsgreek.xml",encoding="utf-8").read()
    def inline(x):
        x=re.sub(r'<greek [^>]*unicode="([^"]*)"[^>]*/>',r"\1",x)
        x=re.sub(r'<latin>(.*?)</latin>',r"\1",x)
        def sref(m):
            lang,n=re.search(r'language="(\w+)"',m.group(0)).group(1),int(re.search(r'strongs="0*(\d+)"',m.group(0)).group(1))
            return ("H" if lang=="HEBREW" or n>5624 else "G")+str(n)
        x=re.sub(r"<strongsref [^>]*/>",sref,x)
        x=re.sub(r"<[^>]+>","",x)
        return re.sub(r"\s+"," ",html.unescape(x)).strip()
    o={}
    for m in re.finditer(r'<entry strongs="0*(\d+)">(.*?)</entry>',t,flags=re.S):
        n,e=m.groups();key="G"+n
        g=re.search(r'<greek [^>]*unicode="([^"]*)"[^>]*translit="([^"]*)"',e)
        pr=re.search(r'<pronunciation strongs="([^"]*)"',e)
        f=lambda tag:(lambda r:inline(r.group(1)) if r else "")(re.search(f"<{tag}>(.*?)</{tag}>",e,flags=re.S))
        kjv=f("kjv_def").lstrip(":-").strip().rstrip(".")
        tail=e[e.index("</kjv_def>")+10:] if "</kjv_def>" in e else ""
        tail=inline(re.sub(r"<see [^>]*/>","",tail))
        fb=fallback.get(key,["","","","","",""])
        o[key]=[g.group(1) if g else fb[0],g.group(2) if g else fb[1],pr.group(1) if pr else "",
                f("strongs_derivation") or fb[3],f("strongs_def") or fb[4],(kjv+(". "+tail if tail else "")).strip()]
    return o

# ---------------------------------------------------------------- BDB
def go_attr(b,c,v):
    try: book=PROT[int(b)-1];c=int(c);v=int(v)
    except Exception: return None
    ks=to_kjv("org",book,c,v)
    if not ks: return None
    bk,kc,kv=ks[0]
    return f"{bk}|{kc}|{kv}"

def bdb_ref(m):
    a=dict(re.findall(r'(\w+)="([^"]*)"',m.group(1)));txt=m.group(2)
    g=go_attr(a.get("b"),a.get("cBegin"),a.get("vBegin"))
    if not g: return txt
    return f'<button class="xref" data-k="{g}">{txt}</button>'

def bdb_clean(h):
    h=re.sub(r"<h1>.*?</h1>","",h,flags=re.S)
    h=re.sub(r'<div class="navigation">.*?</div>',"",h,flags=re.S)
    h=re.sub(r"<placeholder\d+/>",'<span class="ph" title="Script not shown">…</span>',h)
    h=re.sub(r"<(checkingNeeded|wrongReferenceRemoved)/>","",h)
    h=re.sub(r"<ref ([^>]*)>(.*?)</ref>",bdb_ref,h,flags=re.S)
    for a,b in (("bdbheb",'span lang="he"'),("bdbarc",'span lang="he" class="arc"'),("grk",'span lang="el"'),("highlightword","b"),("highlight","i")):
        h=h.replace(f"<{a}>",f"<{b}>").replace(f"</{a}>",f"</{b.split()[0]}>")
    h=re.sub(r"</?(transliteration|reflink|big)>","",h)
    h=re.sub(r"<lookup[^>]*>(.*?)</lookup>",r'<span class="ab">\1</span>',h,flags=re.S)
    h=re.sub(r"<entry[^>]*>(.*?)</entry>",r"\1",h,flags=re.S)
    h=re.sub(r'<div class="(section|point|remarks)">',lambda m:f'<div class="bdb-{m.group(1)[:3]}">',h)
    h=re.sub(r"<hr>","",h)
    h=h.replace("<p>",'<div class="bdb-p">').replace("</p>","</div>")
    h=re.sub(r"\s+onclick=\"[^\"]*\"","",h)
    h=h.replace("\\&emsp;","&emsp;").replace("\\"," ")
    h=re.sub(r"«[^»]*»","",h)
    h=re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]","",h)
    h=re.sub(r"[ \t]{2,}"," ",h).strip()
    left=set(re.findall(r"<(\w+)",h))-{"span","button","b","i","sup","sub","div","br","u"}
    assert not left,left
    return h

def bdb():
    csv.field_size_limit(10**9)
    rows=list(csv.reader(open(SCR+"bdb/unabridged-BDB-Hebrew-lexicon.csv",encoding="utf-8"),delimiter="\t"))[1:]
    d=collections.defaultdict(list)
    for bid,sn,content in rows:
        if not sn: continue
        for s in re.findall(r"H\d+",sn):
            d["H"+str(int(s[1:]))].append(bdb_clean(content))
    n=chunked(d,"bdb")
    return len(d),n

# ---------------------------------------------------------------- Middle Liddell
def bare(s):
    s=unicodedata.normalize("NFD",s.lower())
    s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^α-ω]","",s.replace("ς","σ"))
def nfc(s): return unicodedata.normalize("NFC",re.sub(r"[\d\-]","",s)).lower().replace("ς","σ")

def uni(t):
    t=re.sub(r"\d+$","",t.strip()) if re.fullmatch(r"[^\s]+\d",t.strip()) else t
    return beta.beta_to_uni(t)

def ml_html(el,greek=False):
    """TEI element -> HTML string."""
    tag=el.tag;g=greek or el.get("lang")=="greek"
    def txt(s): return html.escape(uni(s) if g else s,quote=False) if s else ""
    inner=txt(el.text)+"".join(ml_html(c,g)+txt_tail(c,g) for c in el)
    if tag in ("gramGrp",): return ""
    if tag=="orth": return f'<b lang="el" class="ml-hw">{inner}</b>'
    if tag in ("tr",): return f"<b>{inner}</b>"
    if tag=="usg": return f'<span class="ml-au">{re.sub(r"^id=.*","id.",inner)}</span>'
    if tag=="sense":
        n=el.get("n","");lv=el.get("level","1")
        lab=f"<b>{html.escape(n)}.</b> " if n and n not in ("0",) else ""
        return f'<div class="ml-s ml-l{lv}">{lab}{inner}</div>'
    if tag=="etym": return f'<span class="ml-et">[{inner}]</span>'
    if g and tag in ("foreign","ref","form","note","xr"): return f'<span lang="el">{inner}</span>' if tag in ("foreign","ref") else inner
    return inner
def txt_tail(c,g):
    t=c.tail or ""
    return html.escape(t,quote=False)

def ml_entries():
    t=open(SCR+"middle-liddell/Perseus_text_1999.04.0058.xml",encoding="utf-8").read()
    E=[]
    for m in re.finditer(r'<entry key="([^"]*)"[^>]*>.*?</entry>',t,flags=re.S):
        try: el=ET.fromstring(m.group(0))
        except ET.ParseError: continue
        key=uni(m.group(1))
        body=ml_html(el)
        body=re.sub(r"\s+"," ",body).strip()
        E.append((key,body))
    return E

def middle_liddell(strong_g):
    E=ml_entries()
    exact=collections.defaultdict(list);loose=collections.defaultdict(list)
    for i,(k,b) in enumerate(E):
        exact[nfc(k)].append(i);loose[bare(k)].append(i)
    step=json.load(open(os.path.join(OUT,"..","lex-grk.json")))
    lem={}
    for g,(lemma,*_) in strong_g.items(): lem.setdefault(g,[]).append(lemma)
    for g,key in step["b"].items():
        e=step["e"].get(key)
        if e: lem.setdefault(g,[]).append(e[0])
    d={};miss=[]
    for g,ls in lem.items():
        hit=[]
        for l in ls:
            l=l.split(",")[0].strip()
            hit=exact.get(nfc(l)) or []
            if hit: break
        if not hit:
            for l in ls:
                hit=loose.get(bare(l.split(",")[0])) or []
                if hit: break
        if hit: d[g]=[E[i][1] for i in hit]
        else: miss.append(g)
    n=chunked(d,"ml")
    return len(E),len(d),len(miss),n,miss[:30]

if __name__=="__main__":
    S=strongs();print("strongs",{k:len(v) for k,v in S.items()})
    print("bdb",bdb())
    print("ml",middle_liddell(S["grk"]))
