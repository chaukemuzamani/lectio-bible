"""Cross-references and commentaries for every verse.

    python3 study.py

Sources
  Cross-references  OpenBible.info (CC BY, 2024-11-04; reader votes) via github.com/scrollmapper/bible_databases
                    Treasury of Scripture Knowledge (public domain), CrossWire TSK 1.4
  Commentaries      Matthew Henry (complete, MHC 2.2), Jamieson-Fausset-Brown (JFB 3.0), Albert Barnes (NT, Barnes 1.1),
                    Adam Clarke (Clarke 2.0), C. H. Spurgeon's Treasury of David (TDavid 2.1): CrossWire SWORD modules,
                    public domain, as packaged (SHA-256 pinned) by github.com/CalvinMagezi/berea release commentary-1;
                    John Gill (public domain) from the Free Use Bible API, as released by github.com/joathanmf/bibliaco-dados.

Writes ../data/study/  (book = index in PROT, verses in KJV numbering)
  xref/<book>.json    {"c:v": [[target, votes], ...]}  target "b.c.v" or "b.c.v-b.c.v", most votes first
  tsk/<book>.json     {"c:v": [[keyword, [[label, "Book|c|v"], ...]], ...]}
  <code>/<book>.json  {"c": [[from, to, html], ...]}   from/to = verses (0 = introduction); chapter "0" = book introduction
"""
import os,re,json,html,sqlite3,collections
from vrs import PROT
SCR="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/comm/"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","study")
COMM=[("MH","MHC","mhc"),("JFB","JFB","core"),("BA","Barnes","barnes"),("CL","Clarke","clarke"),("TD","TDavid","tdavid")]

# ------------------------------------------------------------------ book names in all the commentaries' styles
NAMES={0:"genesis gen ge gn",1:"exodus exod exo ex",2:"leviticus lev le lv",3:"numbers num nu nm nb",4:"deuteronomy deut deu de dt",
 5:"joshua josh jos jsh",6:"judges judg jdg jg jud",7:"ruth ru rth",8:"1samuel 1sam 1sa 1s",9:"2samuel 2sam 2sa 2s",10:"1kings 1kgs 1ki 1k",
 11:"2kings 2kgs 2ki 2k",12:"1chronicles 1chron 1chr 1ch",13:"2chronicles 2chron 2chr 2ch",14:"ezra ezr",15:"nehemiah neh ne",16:"esther esth est es",
 17:"job jb",18:"psalms psalm psa ps pss",19:"proverbs prov pro pr prv",20:"ecclesiastes eccles eccl ecc ec qoh",
 21:"songofsolomon songofsongs song sos so canticles cant sol",22:"isaiah isa is",23:"jeremiah jer jr je",24:"lamentations lam la",
 25:"ezekiel ezek eze ezk",26:"daniel dan da dn",27:"hosea hos ho",28:"joel joe jl",29:"amos amo am",30:"obadiah obad ob",31:"jonah jon jnh",
 32:"micah mic mi",33:"nahum nah na",34:"habakkuk hab hb",35:"zephaniah zeph zep zp",36:"haggai hag hg",37:"zechariah zech zec zac zc",
 38:"malachi mal ml",39:"matthew matt mat mt",40:"mark mar mrk mk mr",41:"luke luk lk lu",42:"john joh jhn jn",43:"acts act ac",
 44:"romans rom ro rm",45:"1corinthians 1cor 1co",46:"2corinthians 2cor 2co",47:"galatians gal ga",48:"ephesians eph ep",
 49:"philippians phil php pp",50:"colossians col co",51:"1thessalonians 1thess 1thes 1th",52:"2thessalonians 2thess 2thes 2th",
 53:"1timothy 1tim 1timm 1ti 1tm",54:"2timothy 2tim 2ti 2tm",55:"titus tit",56:"philemon philem phm phlm",57:"hebrews heb he",58:"james jas jam jm",
 59:"1peter 1pet 1pe 1pt",60:"2peter 2pet 2pe 2pt",61:"1john 1jn 1jo 1joh 1jno",62:"2john 2jn 2jo 2joh",63:"3john 3jn 3jo 3joh",64:"jude jud",
 65:"revelation rev re rv apocalypse"}
ALIAS={}
for b,s in NAMES.items():
    for a in s.split():
        if a=="jud" and b==64: continue                 # “Jud” is Judges in these commentaries; Jude is written out
        ALIAS.setdefault(a,b)
ROMAN={"i":"1","ii":"2","iii":"3","first":"1","second":"2","third":"3"}
BOOKRE=re.compile(r"(?<![\w])((?:(?:[123]|I{1,3}|First|Second|Third)\s?)?(?:Song of Solomon|Song of Songs|[A-Z][a-z]{0,13})\.?)\s(\d{1,3}):(\d{1,3})(?:\s?[-–]\s?(\d{1,3})(?!:))?")
CONT=re.compile(r"""^(\s*[,;]\s*(?:and\s+)?)(\d{1,3})(?::(\d{1,3}))?(?:\s?[-–]\s?(\d{1,3})(?!:))?(?![\d:]|\s?[a-z]{2})""")
CHAPS=None
def chapters():
    global CHAPS
    if CHAPS is None:
        from lib import load
        K=load("KJVS");CHAPS={PROT.index(b):[len(c) for c in chs] for b,chs in K.items() if b in PROT}
    return CHAPS
def valid(b,c,v):
    ch=chapters().get(b);return bool(ch) and 1<=c<=len(ch) and 1<=v<=ch[c-1]
def book_of(tok):
    t=tok.strip().rstrip(".").lower()
    m=re.match(r"(i{1,3}|first|second|third)\s?(.*)",t)
    if m and m.group(2): t=ROMAN[m.group(1)]+m.group(2)
    return ALIAS.get(t.replace(" ",""))

def btn(b,c,v,label): return f'<button class="xref" data-k="{PROT[b]}|{c}|{v}">{label}</button>'

def linkify(text,ctx=None):
    """Escape plain text and turn verse references into buttons. ctx=(book,chapter) lets bare “15” or “7:47” refer to it (TSK)."""
    out=[];pos=0;T=text
    def chain(i,b,c):
        """continuations after a reference: “; 8:32”, “, 19”, “,10-12” """
        res=[]
        while True:
            m=CONT.match(T[i:])
            if not m: break
            sep,a1,a2,a3=m.groups()
            if a2: cc,vv=int(a1),int(a2)
            else:
                if ";" in sep and ctx is None: break         # “; 5” after a reference in prose is usually not a verse
                cc,vv=c,int(a1)
            if not valid(b,cc,vv): break
            label=T[i+len(sep):i+m.end()]
            res.append((i,i+len(sep),i+m.end(),b,cc,vv,label));i+=m.end();c=cc
        return res,i
    for m in BOOKRE.finditer(T):
        if m.start()<pos: continue
        b=book_of(m.group(1))
        if b is None: continue
        c,v=int(m.group(2)),int(m.group(3))
        if not valid(b,c,v): continue
        out.append(html.escape(T[pos:m.start()],quote=False))
        out.append(btn(b,c,v,html.escape(m.group(0),quote=False)))
        res,end=chain(m.end(),b,c)
        for s,ls,e,bb,cc,vv,label in res:
            out.append(html.escape(T[s:ls],quote=False));out.append(btn(bb,cc,vv,html.escape(label,quote=False)))
        pos=end
    out.append(html.escape(T[pos:],quote=False))
    return "".join(out)

def paras(t):
    t=t.replace("\r","").strip()
    ps=[p.strip() for p in re.split(r"\n\s*\n|\n",t) if p.strip()]
    return "".join(f"<p>{p}</p>" for p in ps)

def write(sub,data):
    os.makedirs(f"{OUT}/{sub}",exist_ok=True)
    for b,d in data.items():
        json.dump(d,open(f"{OUT}/{sub}/{b}.json","w"),ensure_ascii=False,separators=(",",":"))
def write_chapters(code,data):
    """commentaries: one file per chapter, <code>/<book>/<chapter>.json = [[from, to, html], …]; index.json lists what exists"""
    have={}
    for b,chs in data.items():
        os.makedirs(f"{OUT}/{code}/{b}",exist_ok=True)
        for ch,entries in chs.items():
            json.dump(entries,open(f"{OUT}/{code}/{b}/{ch}.json","w"),ensure_ascii=False,separators=(",",":"))
        have[b]=sorted(int(c) for c in chs)
    return have

# ------------------------------------------------------------------ OpenBible cross-references
OSIS={"Gen":0,"Exod":1,"Lev":2,"Num":3,"Deut":4,"Josh":5,"Judg":6,"Ruth":7,"1Sam":8,"2Sam":9,"1Kgs":10,"2Kgs":11,"1Chr":12,"2Chr":13,"Ezra":14,
 "Neh":15,"Esth":16,"Job":17,"Ps":18,"Prov":19,"Eccl":20,"Song":21,"Isa":22,"Jer":23,"Lam":24,"Ezek":25,"Dan":26,"Hos":27,"Joel":28,"Amos":29,
 "Obad":30,"Jonah":31,"Mic":32,"Nah":33,"Hab":34,"Zeph":35,"Hag":36,"Zech":37,"Mal":38,"Matt":39,"Mark":40,"Luke":41,"John":42,"Acts":43,
 "Rom":44,"1Cor":45,"2Cor":46,"Gal":47,"Eph":48,"Phil":49,"Col":50,"1Thess":51,"2Thess":52,"1Tim":53,"2Tim":54,"Titus":55,"Phlm":56,"Heb":57,
 "Jas":58,"1Pet":59,"2Pet":60,"1John":61,"2John":62,"3John":63,"Jude":64,"Rev":65}
def osis(r):
    b,c,v=r.split(".");return OSIS[b],int(c),int(v)
def openbible():
    D=collections.defaultdict(lambda:collections.defaultdict(list));n=0
    for line in open(SCR+"sm/sources/extras/cross_references.txt",encoding="utf-8"):
        if line.startswith("From") or not line.strip(): continue
        f,t,votes=line.rstrip("\n").split("\t");votes=int(votes)
        if votes<1: continue                                   # readers voted it down
        b,c,v=osis(f)
        if "-" in t:
            a,z=t.split("-");ab,ac,av=osis(a);zb,zc,zv=osis(z);tgt=f"{ab}.{ac}.{av}-{zb}.{zc}.{zv}"
        else:
            tb,tc,tv=osis(t);tgt=f"{tb}.{tc}.{tv}"
        D[b][f"{c}:{v}"].append([tgt,votes]);n+=1
    for b in D:
        for k in D[b]: D[b][k].sort(key=lambda x:-x[1])
    write("xref",D);return n

# ------------------------------------------------------------------ Treasury of Scripture Knowledge
def tsk_refs(line,b,c):
    """“1:14,18; Ge 22:12; Mr 12:6; *marg:” in the context of book b, chapter c → [[label, "Book|c|v"], …]; notes are skipped"""
    res=[];cb,cc=b,c
    for part in re.split(r";\s*",line.strip().rstrip(".")):
        part=part.strip()
        if not part or part.startswith("*"): continue
        m=re.match(r"((?:[123]\s?)?[A-Za-z][a-z]{0,12}\.?)\s+(\d.*)",part)
        if m:
            nb=book_of(m.group(1))
            if nb is None: continue
            cb=nb;rest=m.group(2)
        elif re.match(r"\d",part): rest=part
        else: continue
        mm=re.match(r"(?:(\d+):)?(\d+)(?:-(?:\d+:)?\d+)?((?:,\s?\d+(?:-\d+)?)*)",rest)
        if not mm: continue
        v=int(mm.group(2))
        if mm.group(1): cc=int(mm.group(1))
        elif m:
            if len(chapters().get(cb,[]))==1: cc=1          # a one-chapter book: “Jude 3”, “Ob 15”
            else: cc,v=v,1                                  # a whole chapter: “Ps 23”
        if valid(cb,cc,v): res.append([(m.group(1)+" " if m else "")+mm.group(0),f"{PROT[cb]}|{cc}|{v}"])
    return res

def tsk():
    c=sqlite3.connect(SCR+"berea/commentary-core.sqlite");D=collections.defaultdict(dict);n=0
    for b,ch,vs,txt in c.execute("select book,chapter,verse_start,html_or_text from entries where module='TSK'"):
        b-=1
        if not(0<=b<66) or vs<1: continue
        lines=[l.strip() for l in txt.split("\n") if l.strip()]
        groups=[];kw=None
        for l in lines:
            if re.match(r"^\d+\s+[A-Za-z]",l) and book_of(l.split()[1]) is None: continue   # chapter outline line (“1 David's confidence …”)
            refs=tsk_refs(l,b,ch) if re.match(r"^((?:[123]\s?)?[A-Z][a-z]{0,12}\.?\s+)?\d",l) else None
            if refs:
                groups.append([kw or "",refs]);kw=None;n+=len(refs)
            else: kw=l.rstrip(".")
        if groups: D[b][f"{ch}:{vs}"]=groups
    write("tsk",D);return n

# ------------------------------------------------------------------ commentaries
def commentaries():
    stats={}
    for code,mod,pack in COMM:
        c=sqlite3.connect(SCR+f"berea/commentary-{pack}.sqlite");D=collections.defaultdict(lambda:collections.defaultdict(list));n=0
        for b,ch,vs,ve,txt in c.execute("select book,chapter,verse_start,verse_end,html_or_text from entries where module=? order by book,chapter,verse_start",(mod,)):
            b-=1
            if not(0<=b<66): continue
            D[b][str(ch)].append([vs,max(vs,ve),paras(linkify(txt))]);n+=1
        HAVE[code]=write_chapters(code,D);stats[code]=n
    # Gill
    D=collections.defaultdict(lambda:collections.defaultdict(list));n=0
    from vrs import USFM
    for line in open(SCR+"gill/john-gill.en.jsonl",encoding="utf-8"):
        x=json.loads(line)
        if x["book"] not in USFM: continue
        b=USFM.index(x["book"])
        D[b][str(x["chapter"])].append([x["start_verse"],max(x["start_verse"],x["end_verse"] or 0),paras(linkify(x["text"]))]);n+=1
    for b in D:
        for ch in D[b]: D[b][ch].sort(key=lambda e:(e[0],e[1]))
    HAVE["GI"]=write_chapters("GI",D);stats["GI"]=n
    json.dump(HAVE,open(f"{OUT}/index.json","w"),separators=(",",":"))
    return stats
HAVE={}

if __name__=="__main__":
    import shutil
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    print("OpenBible cross-references:",openbible())
    print("TSK references:",tsk())
    print("commentary entries:",commentaries())
