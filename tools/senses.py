"""Which meaning of a word is used in which verse — from the verse references the lexicons give under each sense.

    python3 senses.py

Greek: Abbott-Smith (the STEPBible brief lexicon text) — “__1. <b>the tongue</b>: Mrk.7:33 …  __2. <b>a tongue, language</b>: Act.2:4 …”
Hebrew: BDB (data/lex/bdb) — “<b>1.</b> <i>tongue</i> of men … [Judges 7:5] …  <b>2.</b> …”
Writes data/lex/senses-grk.json and data/lex/senses-heb.json:
    {"G1100": [["the tongue", "a tongue, language"], {"43.2.4": 1, ...}], ...}
Verse keys are "bookIndex.chapter.verse" in KJV numbering; values index the label list.
"""
import os,re,json,glob,html,collections
from vrs import PROT
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA=os.path.join(ROOT,"data")

NT_ABBR={"Mat":"Matthew","Mrk":"Mark","Luk":"Luke","Jhn":"John","Act":"Acts","Rom":"Romans","1Co":"I Corinthians","2Co":"II Corinthians",
 "Gal":"Galatians","Eph":"Ephesians","Php":"Philippians","Col":"Colossians","1Th":"I Thessalonians","2Th":"II Thessalonians","1Ti":"I Timothy",
 "2Ti":"II Timothy","Tit":"Titus","Phm":"Philemon","Heb":"Hebrews","Jas":"James","1Pe":"I Peter","2Pe":"II Peter","1Jo":"I John","1Jn":"I John",
 "2Jo":"II John","2Jn":"II John","3Jo":"III John","3Jn":"III John","Jud":"Jude","Jde":"Jude","Rev":"Revelation of John"}
for b in NT_ABBR.values(): assert b in PROT,b

def plain(s):
    s=re.sub(r"<br\s*/?>"," ",s);s=re.sub(r"<[^>]+>","",s)
    return re.sub(r"\s+"," ",html.unescape(s)).strip()

def clean_label(s,maxlen=60):
    s=re.sub(r"\s+"," ",s).replace("\xad","").strip().strip(",;:. ")
    if s.count("(")>s.count(")"): s=s[:s.rindex("(")].strip(" ,;:.")
    return s if 0<len(s)<=maxlen and re.match(r"\w",s) else None

# ------------------------------------------------------------------ Greek
REF=re.compile(r"\b([1-3]?[A-Z][a-z]{1,2})[. ](\d+):(\d+)")
CONT=re.compile(r"""^["'\]\)]*(?:,\s*|\s+)(?:(\d+):(\d+)|(\d+)(?:-(\d+))?)(?![\d:])""")
def greek_refs(text):
    out=[];pos=0
    for m in REF.finditer(text):
        if m.start()<pos: continue
        bk=NT_ABBR.get(m.group(1))
        if not bk: continue
        bi=PROT.index(bk);c=int(m.group(2));v=int(m.group(3));out.append((bi,c,v));pos=m.end()
        while True:
            n=CONT.match(text[pos:])
            if not n: break
            if n.group(1): c=int(n.group(1));v=int(n.group(2));out.append((bi,c,v))
            else:
                a=int(n.group(3));b=int(n.group(4) or a)
                if b<a or b-a>40: break
                out.extend((bi,c,x) for x in range(a,b+1))
            pos+=n.end()
    return out

NOTE_RE=re.compile(r"(?i)^(trans|intrans|in-trans|in\b|as\b|by\b|c\.|later|generally|properly|prop\b|metaph|meton|adverb|adv\b|prep|defin|with\b|absol|pass\b|mid\b|act\b|cl\b|causal|esp|after\b|neut|perfective|pl\b|sing|gen\b|dat\b|acc)")
QUAL_RE=re.compile(r"(?i)^(of|with|in|as|after|before|absol|pass|mid|trans|intrans|c\.|by|at|for|on|from|to the|in a|in the)\b")
GREEKCH=re.compile(r"[Ͱ-Ͽἀ-῿]")
def sense_label(part):
    """Name of a (sub-)sense from its own text: its first bold words, else its definition text, skipping grammar notes."""
    bb=re.search(r"<b>([^<]+)</b>",part)
    if bb:
        lab=clean_label(plain(bb.group(1)))
        if lab: lab=tidy(lab)
        pre=plain(part[:bb.start()]).strip(" ,;:")             # “of persons, <b>faithful, trusty</b>” → keep the qualifier
        if re.search(r"(?i)\b(the|a|an|of)$",pre): pre=""        # “Of the <b>Holy Spirit</b>” is not a qualifier
        if lab and pre and len(pre)<=24 and QUAL_RE.match(pre) and not GREEKCH.search(pre) and not NOTE_RE.match(pre):
            lab=f"{lab} ({pre})"
        return lab
    head=re.split(r"[:;]|,\s*(?:with|c\.)\s",plain(part))[0].strip()
    head=re.sub(r"\s+[A-Z][a-z]{1,3}\.\d.*$","",head)             # trailing verse reference
    if not head or GREEKCH.search(head[:3]): return None
    to=re.search(r"(?:^|,\s*)(to\s.+)$",head)
    if NOTE_RE.match(head) or len(head)<4:
        return tidy(clean_label(to.group(1)) or "") or None if to else None
    h=clean_label(head);return tidy(h) if h else None

def is_qualifier(lab): return bool(lab) and (len(lab)<=32 or bool(re.match(r"(?i)of\s",lab))) and bool(QUAL_RE.match(lab))
def has_bold(part): return bool(re.search(r"<b>[^<]+</b>",part))

USAGE_RE=re.compile(r"(?i)^(anarthrous|epanaleptic|special idioms?|in general|generally|more freq|with(out)? (the )?art|absol|esp\b|chiefly|freq)")
def usage_like(lab): return bool(lab) and (is_qualifier(lab) or bool(NOTE_RE.match(lab)) or bool(USAGE_RE.match(lab)))
def tidy(lab):
    lab=re.sub(r"\s*\([^()]*(?:\d|cl\.|Hom|Plat|LXX|Arist|Polyb|Xen|Luc|al\.|MM|Bl\.|see)[^()]*\)","",lab)   # citations
    lab=re.sub(r",?\s*[1-3]?[A-Z][a-z]{1,2}\.\d[\d:,\s-]*","",lab)                                          # verse references
    return re.sub(r"\s+"," ",lab).strip(" ,;:.")
def lowerfirst(q): return q[:1].lower()+q[1:] if q[:2]!=q[:2].upper() else q
def compose(core,quals):
    quals=[tidy(q) for q in quals if q and tidy(q)]
    core=tidy(core) if core else None
    if not core: return None
    m=re.match(r"^(.*?)\s*\(([^()]*)\)$",core)                 # “God (of the one true)” + “anarthrous” → one bracket
    if m and quals: core,quals=m.group(1),[m.group(2)]+quals
    quals=[q for i,q in enumerate(quals) if q.lower() not in [x.lower() for x in quals[:i]] and q.lower() not in core.lower()]
    return core+(" ("+"; ".join(lowerfirst(q) for q in quals)+")" if quals else "")

def greek():
    """Items are the numbered senses, or their lettered sub-senses (“2a”) where Abbott-Smith divides them —
    the verse references sit under the sub-senses, so the marker can point at exactly the right one.
    A name is the definition, with usage notes (“of persons”, “in general”) in brackets after it."""
    lex=json.load(open(f"{DATA}/lex-grk.json"));res={}
    for g,key in lex["b"].items():
        e=lex["e"].get(key)
        if not e or not e[4]: continue
        t=e[4].replace("<br>","\n")
        parts=re.split(r"__\s*(\d+)\.",t)
        if len(parts)<5: continue
        nums=[int(parts[i]) for i in range(1,len(parts),2)]
        if nums!=list(range(1,len(nums)+1)): continue
        gloss=clean_label(re.sub(r"[/:].*","",e[3] or ""))
        verb=":V" in (e[2] or "")
        def usage(l): return usage_like(l) or (bool(l) and not verb and l.lower().startswith("to "))
        def build(with_subs):
            items=[];vmap={}
            for i in range(1,len(parts),2):
                n=int(parts[i]);seg=parts[i+1]
                sp=re.split(r"__\s*\(([a-z])\)",seg) if with_subs else [seg]
                own=sp[0];plab=sense_label(own)
                pdef=None if usage(plab) else plab;pq=plab if usage(plab) else None
                subs=[(sp[j],sp[j+1]) for j in range(1,len(sp),2)]
                if len(subs)<2:
                    lab=compose(pdef or (sense_label(subs[0][1]) if subs and not usage(sense_label(subs[0][1])) else None) or gloss,[pq])
                    if not lab: return None
                    items.append((str(n),lab))
                    for bi,c,v in greek_refs(plain(seg)): vmap.setdefault(f"{bi}.{c}.{v}",len(items)-1)
                    continue
                group=[]
                for letter,txt in subs:
                    sl=sense_label(txt);bold=has_bold(txt)
                    if sl and (usage(sl) or (not bold and pdef)): sdef,sq=None,(sl if usage(sl) else None)
                    else: sdef,sq=sl,None
                    lab=compose(sdef or pdef or gloss,[pq,sq])
                    if not lab: continue
                    refs=greek_refs(plain(txt))
                    if group and group[-1][1]==lab: group[-1][2].extend(refs)
                    else: group.append([f"{n}{letter}",lab,refs])
                if not group: return None
                if len(group)==1: group[0][0]=str(n)
                for k2,lab,refs in group:
                    items.append((k2,lab))
                    for bi,c,v in refs: vmap.setdefault(f"{bi}.{c}.{v}",len(items)-1)
            keys=[k for k,_ in items];labs=[l for _,l in items]
            if len(set(keys))!=len(keys) or len(items)<2 or len(set(labs))<2: return None
            return items,vmap
        r=build(True) or build(False)
        if not r: continue
        items,vmap=r
        res[g]=[[l for _,l in items],vmap,[k for k,_ in items]]
    return res

# ------------------------------------------------------------------ Hebrew
def bdb_entries():
    E={}
    for f in glob.glob(f"{DATA}/lex/bdb/*.json"): E.update(json.load(open(f)))
    return E

HEB_CHARS=re.compile(r"[\u0590-\u05FF\uFB1D-\uFB4F]+")
def bdb_label(seg):
    head=re.split(r'<button|<br|;|—|\[|:|\|\|',seg,maxsplit=1)[0]
    t=HEB_CHARS.sub("",plain(head)).replace("׳","")
    t=re.sub(r"\((?:[^()]*\d[^()]*|and late|late|rare|poetry|poet\.?)\)","",t)      # (33 t.), (and late) …
    t=re.sub(r"\s+"," ",t)
    t=re.sub(r"^[=\s,.]+","",t)
    t=re.sub(r"^(?:(?:occasionally|usually|rarely|especially|often|chiefly|also|so|hence|then|sometimes|perhaps|probably|=)[\s,]*)+","",t,flags=re.I)
    t=re.sub(r"^[=\s,.]+","",t).strip(" ,.;=")
    if t.count("(")!=t.count(")"): t=t.split("(")[0].strip(" ,.;")
    if not t or not re.match(r"[(A-Za-z]",t):
        i=re.search(r"<i>([^<]{2,48})</i>",seg[:400]);t=i.group(1).strip(" ,.;-") if i else ""
    if len(t)>48: t=t[:48].rsplit(" ",1)[0].rstrip(" ,;")+"…"
    return t if re.match(r"[(A-Za-z]",t or "") else None

def bdb_parse(h):
    parts=re.split(r"<b>(\d+)\.</b>",h)
    if len(parts)<5: return None
    nums=[int(parts[i]) for i in range(1,len(parts),2)]
    if nums!=list(range(1,len(nums)+1)): return None   # verbs restart numbering per stem
    labels=[];vmap={}
    for i in range(1,len(parts),2):
        seg=parts[i+1];labels.append(bdb_label(seg))
        for c in re.finditer(r'data-k="([^|"]+)\|(\d+)\|(\d+)"',seg):
            bk,ch,v=c.group(1),int(c.group(2)),int(c.group(3))
            if bk in PROT: vmap.setdefault(f"{PROT.index(bk)}.{ch}.{v}",len(labels)-1)
    return labels,vmap

LETTERS=str.maketrans("ךםןףץ","כמנפצ")
def skeleton(w): return re.sub(r"[^\u05D0-\u05EA]","",w).translate(LETTERS)
def headword(h):
    m=re.search(r'<span lang="he"[^>]*>([^<]+)</span>',h);return skeleton(m.group(1)) if m else ""

STOP=set("of the a an to in and or as on by for with from at be is its his her their used literal literally figurative figuratively".split())
def words(t): return {w.rstrip("s") for w in re.findall(r"[a-z]+",t.lower()) if w not in STOP and len(w)>1}
def map_senses(bdb_labels,step):
    """BDB sense index -> index in the STEP list (whose wording the strip shows)."""
    if len(bdb_labels)==len(step): return list(range(len(step)))
    W=[words(x) for x in step];out=[]
    for l in bdb_labels:
        w=words(l or "")
        sc=[len(w&x)/max(1,len(w)) for x in W]
        best=max(sc) if sc else 0
        out.append(sc.index(best) if best>0 and sc.count(best)==1 else None)
    return out

def hebrew(step_labels):
    """Labels: the STEP brief outline (as shown today); verse → meaning: from BDB's references, mapped onto it."""
    E=bdb_entries();res={}
    lex=json.load(open(f"{DATA}/lex-heb.json"))
    for k,st in step_labels.items():
        key=lex["b"].get(k);lem=skeleton(lex["e"][key][0]) if key and key in lex["e"] else ""
        lst=[h for h in E.get(k,[]) if lem and headword(h) and (headword(h)==lem or (len(lem)>2 and (lem in headword(h) or headword(h) in lem)))]
        cands=[p for p in (bdb_parse(h) for h in lst) if p]
        vmap={}
        if cands:
            labels,bv=max(cands,key=lambda p:len(p[1]))       # the main article: most verse references
            m=map_senses(labels,st)
            vmap={vk:m[i] for vk,i in bv.items() if m[i] is not None}
        res[k]=[st,vmap]
    return res

def step_hebrew_labels():
    """The STEP outline senses as shown in the strip (same rule as the page: level 1 if ≥2, else level 2)."""
    lex=json.load(open(f"{DATA}/lex-heb.json"));out={}
    for g,key in lex["b"].items():
        e=lex["e"].get(key)
        if not e or not e[4]: continue
        t=plain(e[4].replace("<br>","\n"))
        items=[(3 if m.group(3) else 2 if m.group(2) else 1,m.group(4).strip().strip(",;:. "))
               for m in re.finditer(r"(?:^|\s)(\d+)([a-z]?)(\d*)\)\s*(.*?)(?=\s+\d+[a-z]?\d*[a-z]?\)|$)",t)]
        l1=[s for lv,s in items if lv==1];l2=[s for lv,s in items if lv==2]
        L=l1 if len(l1)>=2 else (l2 or l1)
        L=[re.split(r"\s+(?:Aramaic equivalent|Also means|Greek equivalent)",s)[0].strip(" ,.;:") for s in L]
        L=[s for s in L if s and len(s)<=70]
        if len(L)>=2: out[g]=L
    return out

def coverage(res,code):
    """Share of tagged word occurrences (for words with ≥2 senses here) whose verse is cited under a sense."""
    ix=json.load(open(f"{DATA}/{code}/index.json"));tot=hit=0
    for n,nc,i in ix["b"]:
        bi=PROT.index(n)
        for ci,ch in enumerate(json.load(open(f"{DATA}/{code}/{i}.json"))["c"]):
            for vi,v in enumerate(ch):
                if not isinstance(v,list): continue
                for t in v:
                    if isinstance(t,list) and len(t)>=6:
                        k=re.sub(r"^([HG])0*(\d+).*$",r"\1\2",t[5].split("+")[-1])
                        if k in res:
                            tot+=1;hit+=f"{bi}.{ci+1}.{vi+1}" in res[k][1]
    return hit,tot

if __name__=="__main__":
    G=greek();H=hebrew(step_hebrew_labels())
    for name,obj in (("grk",G),("heb",H)):
        json.dump(obj,open(f"{DATA}/lex/senses-{name}.json","w"),ensure_ascii=False,separators=(",",":"))
    print("greek words",len(G),"coverage",coverage(G,"GRK"))
    print("hebrew words",len(H),"coverage",coverage(H,"HEB"))
    for k in ("G1100","G4151","G3056","H3956","H7307","H5315","H1697"):
        o=G.get(k) or H.get(k);print(k,o[0] if o else None,len(o[1]) if o else "")
