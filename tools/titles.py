"""Psalm superscriptions marked as {"d":1} … {"d":0} in every version.

* Versions that number the title as a verse of its own (Hebrew/Greek/Latin/Russian numbering):
  the whole title verse is wrapped.
* Versions that print the title at the start of verse 1 (KJV numbering): the title is cut off
  where the WEB's title ends, found by word alignment, at the nearest full stop or colon.
"""
import sys,os,re;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import wstruct,align_en,sources
from vrs import V,PROT,USFM
TITLE_EN=re.compile(r"^\s*\[?(A Psalm|A Psalme|A psalm|A Song|A song|A Prayer|A prayer|A Maschil|A Michtam|Michtam|Maschil|Shiggaion|A Shiggaion|Praise|For the end|For the Chief|For the chief|For the Leader|For the leader|To the chief|To the Chief|To him that|To the Overseer|Unto the end|Alleluia|Hallelujah|The psalm|The Psalm|A canticle|A Canticle|A gradual|Of David|Of Asaph|By David|A PSALM|A SONG|A PRAYER|TO THE|FOR THE|A MIKTAM|MIKTAM|A CONTEMPLATION|AN INSTRUCTION|OF DAVID|OF ASAPH|BY DAVID|For David|For Solomon|For the sons|Of understanding|For Asaph|For Idithun|Ps of David)\b")
TITLE_RU=re.compile(r"^\s*(Псалом|псалом|Песнь|песнь|Молитва|молитва|Учение|учение|Хвала|хвала|Начальнику|начальнику|Аллилуия|Аллилуиа|Давида|Давиду|Асафа|Асафу|Сынов|В конец|в конец|Похвала|Хвалебная|Хвалебный|Псалом Давиду|Песнь степеней|Песнь восхождения|Молитва Моисея|Молитва Давида|Молитва нищаго|Молитва страждущего|Нищаго)\b")
def title_verse(sysname,c,v):
    """True when verse (c,v) of Psalms in this versification is (part of) the superscription."""
    if sysname=="kjv": return False
    u="PSA"
    for o in V(sysname).org((u,c,v)):
        for e in V("eng").native(o):
            if e[2]==0: return True
    return False
def has_title(toks): return any(isinstance(t,dict) and t.get("d") is not None for t in toks)
def split_at(toks,off):
    """Insert {d:1} at the start and {d:0} at char offset `off` of the flat text."""
    text,_,spans=wstruct.flat(toks)
    out=[{"d":1}];done=False;o=0
    for t in toks:
        if done: out.append(t);continue
        if isinstance(t,str):
            if o+len(t)>=off:
                cut=off-o;a=t[:cut].rstrip();b=t[cut:].lstrip()
                if a: out.append(a)
                out.append({"d":0})
                if b: out.append(b)
                done=True
            else: out.append(t)
            o+=len(t)
        elif isinstance(t,list):
            if len(t)>=6 and o and text[o:o+1]==" ": o+=1
            out.append(t);o+=len(t[0])
            if o>=off and not done: out.append({"d":0});done=True
        else: out.append(t)
    if not done: out.append({"d":0})
    return out
def sentence_end_near(text,tw,g,lo=None,hi=None,radius=4):
    """Character offset just after a full stop / colon near word gap g (inside [lo,hi] when given)."""
    def end_at(h,chars):
        if h<=0 or h>=len(tw): return None
        between=text[tw[h-1][1]:tw[h][0]]
        m=re.search("["+chars+r"]\]?\)?",between)
        return tw[h-1][1]+m.end() if m else None
    if lo is not None:
        for chars in (".:;",",)"):
            cands=[(abs(h-g),e) for h in range(max(1,lo-1),min(len(tw)-1,hi+1)+1) for e in [end_at(h,chars)] if e is not None]
            if cands: return min(cands)[1]
    for d in range(0,radius+1):
        for h in (g-d,g+d):
            e=end_at(h,".:;")
            if e is not None: return e
    return None
_webu=None
def web_title(c):
    global _webu
    if _webu is None: _webu=sources.webu()
    try: v=_webu["Psalms"][c-1][0]
    except Exception: return None
    if not has_title(v): return None
    i=[k for k,t in enumerate(v) if isinstance(t,dict) and t.get("d")==0][0]
    return wstruct.flat(v[:i])[0],wstruct.flat(v)[0]
def mark(books,vsys_ps,lang):
    """Mark the titles in place. vsys_ps: versification of the Psalms in this version."""
    P=books.get("Psalms")
    if not P: return 0
    n=0
    for ci,ch in enumerate(P):
        c=ci+1
        if not ch: continue
        if vsys_ps!="kjv":
            # whole title verses
            tv=[vi for vi in range(min(3,len(ch))) if title_verse(vsys_ps,c,vi+1)]
            if tv and tv==list(range(len(tv))) and len(tv)<len(ch):
                for vi in tv:
                    v=sources.as_tokens(ch[vi])
                    if v and not has_title(v): ch[vi]=[{"d":1}]+v+[{"d":0}];n+=1
                continue
        v=sources.as_tokens(ch[0])
        if not v or has_title(v): continue
        text,_,_=wstruct.flat(v)
        rx=TITLE_RU if lang=="ru" else TITLE_EN
        cut=None
        if lang=="en" and vsys_ps=="kjv":
            wt=web_title(c)
            if wt:
                title,full=wt
                sw=align_en.words(full);tw=align_en.words(text)
                gs=align_en.gap_of(sw,len(title))
                m,ratio=align_en.anchors(sw,tw)
                STOPT={"a","an","the","of","by","to","for","and","in","on","at","he","his","him","when","from","with","set",
                       "i","you","my","me","o","be","that","this","it","upon","unto","lord","god","lord's","say","thou","thee","thy","your"}
                content=[i for i in range(gs) if sw[i][2] not in STOPT]
                tA=[ti for si,ti in m.items() if si<gs and sw[si][2] not in STOPT]     # title words found in this version
                need=1 if len(content)<=3 else max(2,0.3*len(content))
                if ratio>=0.2 and tA and len(tA)>=need:
                    lo,hi,frac=align_en.map_gap(gs,m,len(sw),len(tw))
                    ga=lo+frac*(hi-lo);gr=gs/max(len(sw),1)*len(tw)
                    best=None
                    for h in range(1,len(tw)):
                        between=text[tw[h-1][1]:tw[h][0]]
                        mm=re.search(r"[.:;][\]\)’”'\"]*",between);pen=0
                        if not mm: mm=re.search(r"[,)]\]?",between);pen=3
                        if not mm: continue
                        sc=abs(h-ga)+abs(h-gr)+pen
                        if best is None or sc<best[0]: best=(sc,tw[h-1][1]+mm.end())
                    if best and best[0]<=12 and best[1]>=tw[max(tA)][1]: cut=best[1]
        if cut is None and (vsys_ps!="kjv" or lang=="ru") and rx.match(text):
            m=re.search(r"[.:]\]?\s",text)
            if m and len(text[:m.start()].split())<=30: cut=m.end()-1
        if cut is not None and 0<cut<len(text.rstrip())-3:
            P[ci][0]=split_at(v,cut);n+=1
    return n
