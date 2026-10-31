"""Build the Bible dictionaries: Easton's, Smith's, the ISBE and Hitchcock's Bible Names.

    python3 dictionaries.py

Sources (all public domain texts):
  Easton's Bible Dictionary (1897), Smith's Bible Dictionary (1884), Hitchcock's Bible Names (1869):
      CCEL ThML editions, via github.com/neuu-org/bible-dictionary-dataset (data/00_raw/ccel/xml)
  International Standard Bible Encyclopedia (1915): CrossWire SWORD module ISBE 2.2,
      as converted by github.com/brandonr2630/coc-website (isbe.json)

Writes ../data/dict/:
  index.json            {"t":[[title, key, {"E":chunk,"S":chunk,"I":chunk}, hitchcock-meaning], ...]}  sorted by key
  E/<n>.json, S/<n>.json, I/<n>.json   {key: html}
Verse references become <button class="xref" data-k="Book|c|v"> (KJV numbering, the app maps them to the version
being read); links to other articles become <button class="dsee" data-t="KEY">.
"""
import os,re,json,html,unicodedata
from vrs import PROT
SCR="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/dict/"
CCEL=SCR+"neuu/data/00_raw/ccel/xml/"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","dict")
CHUNK_BYTES=1_600_000

OSIS=["Gen","Exod","Lev","Num","Deut","Josh","Judg","Ruth","1Sam","2Sam","1Kgs","2Kgs","1Chr","2Chr","Ezra","Neh","Esth","Job","Ps","Prov",
 "Eccl","Song","Isa","Jer","Lam","Ezek","Dan","Hos","Joel","Amos","Obad","Jonah","Mic","Nah","Hab","Zeph","Hag","Zech","Mal","Matt","Mark",
 "Luke","John","Acts","Rom","1Cor","2Cor","Gal","Eph","Phil","Col","1Thess","2Thess","1Tim","2Tim","Titus","Phlm","Heb","Jas","1Pet","2Pet",
 "1John","2John","3John","Jude","Rev"]
BOOK=dict(zip(OSIS,PROT))
BOOK.update({"1Macc":"I Maccabees","2Macc":"II Maccabees","3Macc":"III Maccabees","4Macc":"IV Maccabees","Tob":"Tobit","Jdt":"Judith",
 "Wis":"Wisdom","Sir":"Sirach","Bar":"Baruch","1Esd":"I Esdras","2Esd":"II Esdras","PrMan":"Prayer of Manasses","EpJer":"Epistle of Jeremiah",
 "Sus":"Susanna","Bel":"Bel and the Dragon","AddEsth":"Esther (Greek)"})
ISBE_BOOK={b:b for b in PROT}
for n,roman in (("1","I"),("2","II"),("3","III")):
    for b in PROT:
        if b.startswith(roman+" "): ISBE_BOOK[n+" "+b[len(roman)+1:]]=b
ISBE_BOOK["Revelation"]="Revelation of John"

def key(t):
    """Index key: capitals and digits only (“Aaron's Rod” → AARONSROD, “ABEL-BETH-MAACAH” → ABELBETHMAACAH)."""
    t=unicodedata.normalize("NFD",t);t="".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]","",t.upper())

def title_case(t):
    if t!=t.upper(): return t
    return " ".join(w.capitalize() if not re.fullmatch(r"[IVX]+",w) else w for w in t.split(" ")).replace("-"," - ").replace(" - ","-")

def xref(book,c,v,label):
    return f'<button class="xref" data-k="{book}|{c}|{v}">{label}</button>'

# ------------------------------------------------------------------ CCEL ThML (Easton, Smith, Hitchcock)
def ccel_entries(fname):
    t=open(CCEL+fname,encoding="utf-8").read()
    return re.findall(r"<term[^>]*>(.*?)</term>\s*<def[^>]*>(.*?)</def>",t,flags=re.S)

def ccel_html(h):
    def sref(m):
        attrs=m.group(1);label=m.group(2)
        p=re.search(r'parsed="\|([^|]*)\|(\d+)\|(\d+)',attrs)
        if p and p.group(1) in BOOK and int(p.group(2))>0:
            return xref(BOOK[p.group(1)],int(p.group(2)),max(1,int(p.group(3))),label)
        return label
    h=re.sub(r"<scripRef([^>]*)>(.*?)</scripRef>",sref,h,flags=re.S)
    h=re.sub(r"<scripCom[^>]*/>","",h)
    def alink(m):
        href=re.search(r'href="[^"]*\?term=([^"&]+)"',m.group(1))
        if href: return f'<button class="dsee" data-t="{key(html.unescape(href.group(1)).replace("%20"," "))}">{m.group(2)}</button>'
        return m.group(2)
    h=re.sub(r"<a([^>]*)>(.*?)</a>",alink,h,flags=re.S)
    h=re.sub(r'<(p|ul|li|i|b|br)\b[^>]*?(/?)>',lambda m:f"<{m.group(1)}{'/' if m.group(2) else ''}>",h)
    h=re.sub(r"\s+"," ",h).strip()
    left=set(re.findall(r"<(\w+)",h))-{"p","ul","li","i","b","br","button","sup","sub"}
    assert not left,left
    return h

# ------------------------------------------------------------------ ISBE (CrossWire, converted)
def isbe_html(h):
    h=h.replace("\x00","")
    def ref(m):
        b,c,v=m.group(1).split("|");bk=ISBE_BOOK.get(b)
        return xref(bk,int(c),int(v),m.group(2)) if bk else m.group(2)
    h=re.sub(r'<a class="dict-ref" data-r="([^"]+)">(.*?)</a>',ref,h,flags=re.S)
    h=re.sub(r'<a class="dict-see" data-key="([^"]+)">(.*?)</a>',lambda m:f'<button class="dsee" data-t="{key(m.group(1))}">{m.group(2)}</button>',h,flags=re.S)
    h=re.sub(r"\s+"," ",h).strip()
    left=set(re.findall(r"<(\w+)",h))-{"p","b","br","button","i"}
    assert not left,left
    return h

def chunks(entries,code):
    """entries: {key: html}, written in key order to files of about CHUNK_BYTES; returns {key: chunk}."""
    os.makedirs(f"{OUT}/{code}",exist_ok=True)
    where={};cur={};size=0;n=0
    for k in sorted(entries):
        s=len(entries[k].encode())+len(k)+8
        if cur and size+s>CHUNK_BYTES:
            json.dump(cur,open(f"{OUT}/{code}/{n}.json","w"),ensure_ascii=False,separators=(",",":"));n+=1;cur={};size=0
        cur[k]=entries[k];size+=s;where[k]=n
    if cur: json.dump(cur,open(f"{OUT}/{code}/{n}.json","w"),ensure_ascii=False,separators=(",",":"))
    return where,n+1

def build():
    titles={};hitch={};D={}
    def add(code,term,body):
        k=key(html.unescape(re.sub(r"<[^>]+>","",term)))
        if not k: return
        t=title_case(re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",term))).strip())
        if k not in titles or (titles[k]==titles[k].upper() and t!=t.upper()): titles[k]=t
        d=D.setdefault(code,{})
        d[k]=(d[k]+'<hr class="lex-sep">'+body) if k in d else body     # two articles with one heading (e.g. ABEL 1 and 2)
    for term,body in ccel_entries("easton_ebd2.xml"): add("E",term,ccel_html(body))
    for term,body in ccel_entries("smith_bibledict.xml"): add("S",term,ccel_html(body))
    isbe=json.load(open(SCR+"coc/isbe.json",encoding="utf-8"))
    for k0,v in isbe.items(): add("I",v.get("topic") or k0,isbe_html(v["body"]))
    for term,body in ccel_entries("hitchcock_bible_names.xml"):
        k=key(html.unescape(term))
        if k:
            m=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",body))).strip()
            hitch[k]=m if k not in hitch else hitch[k]+"; "+m
            t=title_case(html.unescape(term).strip())
            if k not in titles or titles[k]==titles[k].upper(): titles[k]=t
    if os.path.isdir(OUT):
        import shutil;shutil.rmtree(OUT)
    where={};files=0
    for code in ("E","S","I"):
        w,n=chunks(D[code],code);files+=n
        for k,c in w.items(): where.setdefault(k,{})[code]=c
    allk=set(where)|set(hitch)
    def resolve(t):
        if t in allk: return t
        for v in (t.replace("OR","OUR"),t.replace("OUR","OR"),t+"S",t[:-1] if t.endswith("S") else "",t[:-2] if t.endswith("ES") else "",t.replace("PH","F")):
            if v and v in allk: return v
        pre=sorted(k for k in allk if k.startswith(t) and len(t)>=4)
        return pre[0] if len(pre)==1 else None
    fixed=dead=0
    for code in ("E","S","I"):
        for f in os.listdir(f"{OUT}/{code}"):
            p=f"{OUT}/{code}/{f}";d=json.load(open(p))
            def fix(m):
                nonlocal fixed,dead
                r=resolve(m.group(1))
                if r is None: dead+=1;return m.group(2)
                if r!=m.group(1): fixed+=1
                return f'<button class="dsee" data-t="{r}">{m.group(2)}</button>'
            d={k:re.sub(r'<button class="dsee" data-t="([^"]+)">(.*?)</button>',fix,h) for k,h in d.items()}
            json.dump(d,open(p,"w"),ensure_ascii=False,separators=(",",":"))
    rows=[]
    for k in sorted(allk):
        rows.append([titles.get(k,k.title()),k,where.get(k,{}),hitch.get(k,"")])
    json.dump({"t":rows},open(f"{OUT}/index.json","w"),ensure_ascii=False,separators=(",",":"))
    links=sum(len(re.findall(r'class="xref"',h)) for d in D.values() for h in d.values())
    return {c:len(D[c]) for c in D}|{"names":len(hitch),"headwords":len(rows),"files":files+1,"verse links":links,"see links respelled":fixed,"see links with no article (now plain text)":dead}

if __name__=="__main__":
    print(build())
