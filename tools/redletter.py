"""Words of Jesus in red, worked out ahead of time for every version.

The red stretch is a quotation: it starts at the opening quotation mark of something Jesus says
and ends at its closing mark, so the narrator's words around it ("Jesus looked at him and said")
are never red.

* KJV and WEB (Yahweh ed.) print the red letters themselves.
* Versions whose quotation marks we added know which source quotation each mark belongs to; a
  quotation is red when the WEB prints it red.
* Versions with their own quotation marks: a quotation is red when most of its words line up with
  red words of the WEB (English) or with Greek words the KJV prints red (other languages).
* Greek texts: each word is red when the KJV word with the same Strong's number is red.
"""
import sys,os,re,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import wstruct,quotes,align_en,sources,speech
from vrs import PROT,to_kjv
NT=set(PROT[39:])
BREAK=lambda t:isinstance(t,dict) and (t.get("p") or t.get("br") or t.get("d")==0 or ("l" in t and "h" not in t))

def flat_marks(toks,key="r"):
    """flat text (as wstruct.flat) plus [(offset,value)] for dict tokens carrying `key`."""
    text="";marks=[]
    for t in toks:
        if isinstance(t,str): text+=t
        elif isinstance(t,list):
            if len(t)>=6 and text and not text.endswith(" "): text+=" "
            text+=t[0]
        elif isinstance(t,dict):
            if key in t and not ("h" in t): marks.append((len(text),t[key]))
            if BREAK(t) and text and not text.endswith(" "): text+=" "
    return text,marks

def red_ranges(toks):
    text,marks=flat_marks(toks,"r");out=[];start=None
    for off,v in marks:
        if v==1 and start is None: start=off
        elif v==0 and start is not None: out.append((start,off));start=None
    if start is not None: out.append((start,len(text)))
    return text,out

# ---------- which source quotations are Jesus speaking ----------
ALT_RED={"alt|Acts|9|5|45","alt|Acts|9|6|95","alt|Luke|17|36|0","alt|Mark|12|35|45"}
def red_pids(sp):
    W=sources.load_base("WEBY")
    keys=sorted([k for k in sp if k[0] in NT],key=lambda k:(PROT.index(k[0]),k[1],k[2]))
    ranges={}
    for k in keys:
        if sp[k]["src"]!="WEB": continue
        toks=speech.web_verse(W,*k)
        text,rr=red_ranges(toks)
        ranges[k]=rr
    opens={};closes={}
    for k in keys:
        for off,kind,lvl,pid in sp[k]["ev"]:
            (opens if kind=="o" else closes)[pid]=(k,off)
    order={k:i for i,k in enumerate(keys)}
    out=set(ALT_RED)
    for pid,(ko,oo) in opens.items():
        if pid not in closes or pid.startswith("alt|"): continue
        kc,oc=closes[pid]
        if ko not in order or kc not in order: continue
        red=tot=0
        for i in range(order[ko],order[kc]+1):
            k=keys[i];s=sp[k];text=s["text"]
            a=oo if k==ko else 0;b=oc if k==kc else len(text)
            rr=ranges.get(k,[])
            for j in range(a,b):
                if text[j].isalpha():
                    tot+=1
                    if any(x<=j<y for x,y in rr): red+=1
        if tot and red/tot>=0.5: out.add(pid)
    return out

# ---------- versions with inserted quotation marks ----------
def apply_pids(books,reds):
    """Insert {"r":1}/{"r":0} around quotations whose source quotation is red.
    The first mark of a pair id is its opening mark, the second its closing mark."""
    out={}
    for b,chs in books.items():
        if b not in NT: out[b]=chs;continue
        active=None;nb=[];seen=set()
        for ch in chs:
            nc=[]
            for v in ch:
                v=sources.as_tokens(v);res=[]
                if active: res.append({"r":1})
                for t in v:
                    if isinstance(t,dict) and "q" in t and t.get("pid") and not t.get("ro"):
                        pid=t["pid"]
                        if pid not in seen:
                            seen.add(pid)
                            if active is None and pid in reds:
                                res.append({"r":1});res.append(t);active=pid;continue
                        elif active==pid:
                            res.append(t);res.append({"r":0});active=None;continue
                    res.append(t)
                if active: res.append({"r":0})
                nc.append(tidy_red(res))
            nb.append(nc)
        out[b]=nb
    return out
def tidy_red(v):
    """Drop empty red spans."""
    out=[]
    for t in v:
        if isinstance(t,dict) and t.get("r")==0 and out and isinstance(out[-1],dict) and out[-1].get("r")==1: out.pop();continue
        out.append(t)
    return out

# ---------- versions with their own quotation marks ----------
_weby=None;_kjv=None
def weby():
    global _weby
    if _weby is None: _weby=sources.load_base("WEBY")
    return _weby
def kjv():
    global _kjv
    if _kjv is None: _kjv=sources.load_base("KJVS")
    return _kjv
def weby_red_words(ref):
    toks=speech.web_verse(weby(),*ref)
    text,rr=red_ranges(toks)
    ws=align_en.words(text)
    return ws,[any(x<=w[0]<y for x,y in rr) for w in ws]
def kjv_red_strongs(ref):
    try: toks=kjv()[ref[0]][ref[1]-1][ref[2]-1]
    except Exception: return set(),set()
    red=False;R=set();P=set()
    for t in toks:
        if isinstance(t,dict) and "r" in t: red=bool(t["r"])
        elif isinstance(t,list) and len(t)>1 and t[1]:
            for s in t[1].split(): (R if red else P).add(s)
    return R-P,P-R

def own_pairs(chs):
    """Quotation pairs printed by the version: [(open(ci,vi,off), close(ci,vi,off))]."""
    st=[];pairs=[];sst=[]
    for ci,ch in enumerate(chs):
        for vi,v in enumerate(ch):
            v=sources.as_tokens(v);text,br,_=wstruct.flat(v)
            ev,sst=quotes.scan(text,sst,br);stack=sst
            for off,kind,lvl in [e[:3] for e in ev]:
                if kind=="o":
                    st.append((lvl,(ci,vi,off)))
                elif kind=="c":
                    while st and st[-1][0]>lvl: st.pop()
                    if st and st[-1][0]==lvl:
                        o=st.pop()[1];pairs.append((o,(ci,vi,off+1)))
            # keep the stack in step with the scanner's
            while len(st)>len(stack): st.pop()
    return pairs

def own_quote_red(books,code,lang,vs_of):
    """Red spans for a version that prints its own quotation marks."""
    if lang=="sn":
        import strongs_align as sa
    out={}
    for b,chs in books.items():
        if b not in NT: out[b]=chs;continue
        chs=[[sources.as_tokens(v) for v in ch] for ch in chs]
        cache={}
        def info(ci,vi):
            if (ci,vi) in cache: return cache[(ci,vi)]
            v=chs[ci][vi];text,_,_=wstruct.flat(v)
            refs=[r for r in to_kjv(vs_of(b),b,ci+1,vi+1) if r[0]==b]
            if lang=="en":
                tw=align_en.words(text);flags=[None]*len(tw)
                for r in refs:
                    sw,red=weby_red_words(r)
                    if not sw: continue
                    m,ratio=align_en.anchors(sw,tw)
                    if ratio<0.2: continue
                    for si,ti in m.items(): flags[ti]=red[si]
            else:
                tw=[(m_.start(),m_.end(),m_.group(0)) for m_ in sa.WORDRE[lang].finditer(text)]
                R=set();P=set();S=set()
                for r in refs:
                    a,c=kjv_red_strongs(r);R|=a;P|=c;S|=sa.ref_strongs(*r)
                al=sa.align_words(code,[w[2] for w in tw],S) if tw else {}
                flags=[(True if al.get(i) in R else False if al.get(i) in P else None) for i in range(len(tw))]
            cache[(ci,vi)]=(tw,flags);return cache[(ci,vi)]
        pairs=own_pairs(chs)
        # outermost red pairs
        marks=collections.defaultdict(list)
        covered=[]
        for (o,c) in sorted(pairs):
            if any(a<=o and c<=z for a,z in covered): continue
            red=tot=0
            for ci in range(o[0],c[0]+1):
                for vi in range((o[1] if ci==o[0] else 0),(c[1] if ci==c[0] else len(chs[ci])-1)+1):
                    tw,flags=info(ci,vi)
                    lo=o[2] if (ci,vi)==(o[0],o[1]) else 0
                    hi=c[2] if (ci,vi)==(c[0],c[1]) else 10**9
                    for w,f in zip(tw,flags):
                        if lo<=w[0]<hi and f is not None:
                            tot+=1;red+=f
            if tot>=2 and red/tot>=0.5:
                covered.append((o,c))
        # a quotation interrupted by “Jesus asked” / “he said” continues the speaker's words
        SAYV=re.compile(r"\b(said|says|asked|asks|replied|replies|answered|answers|added|continued|declared|told|cried|exclaimed|went on|saith|spoke)\b",re.I)
        changed=True
        while changed:
            changed=False
            for (o,c) in sorted(pairs):
                if (o,c) in covered or any(a<=o and c<=z for a,z in covered): continue
                for (a,z) in list(covered):
                    for (x,y) in (((c,a)),((z,o))):
                        if x[:2]==y[:2] and 0<=y[2]-x[2]<=60:
                            text,_,_=wstruct.flat(chs[x[0]][x[1]])
                            gap=text[x[2]:y[2]]
                            g2=gap.strip(" ,.;:—”’“‘")
                            if re.fullmatch(r"(?:(?:Jesus|He|he|the Lord|the Master)\s+(?:\w+\s+)?"+"(?:"+SAYV.pattern[3:-3]+")"+r"(?:\s+(?:to|unto)\s+(?:him|her|them|Simon|Peter))?|(?:"+SAYV.pattern[3:-3]+r")\s+(?:Jesus|he|the Lord))",g2,re.I):
                                covered.append((o,c));changed=True;break
                    if changed: break
                if changed: break
        for o,c in covered:
            for ci in range(o[0],c[0]+1):
                for vi in range((o[1] if ci==o[0] else 0),(c[1] if ci==c[0] else len(chs[ci])-1)+1):
                    text,_,_=wstruct.flat(chs[ci][vi])
                    lo=o[2] if (ci,vi)==(o[0],o[1]) else 0
                    hi=c[2] if (ci,vi)==(c[0],c[1]) else len(text)
                    marks[(ci,vi)].append((lo,hi))
        # inside a red quotation, words that line up with the narrator's words in the source stay black
        # (a version's quotation marks are sometimes left open across a verse)
        for key in list(marks):
            ci,vi=key;tw,flags=info(ci,vi)
            text,_,_=wstruct.flat(chs[ci][vi])
            inq=[any(lo<=w[0]<hi for lo,hi in marks[key]) for w in tw]
            red=list(inq)
            i=0
            while i<len(tw):
                if inq[i] and flags[i] is False:
                    j=i;nf=0;last=i
                    while j<len(tw) and inq[j] and flags[j] is not True:
                        if flags[j] is False: nf+=1;last=j
                        j+=1
                    if nf>=2:
                        for k in range(i,last+1): red[k]=False
                    i=j
                else: i+=1
            # words before the first opening quotation mark of the verse are the narrator's,
            # unless the source has them red
            mq=re.search(r"[“‘«„\"'](?=\w)",text)
            if mq:
                pre=[k for k,w in enumerate(tw) if w[0]<mq.start() and red[k]]
                T=sum(1 for k in pre if flags[k] is True);F=sum(1 for k in pre if flags[k] is False)
                if pre and F>=T:
                    for k in pre: red[k]=False
            spans=[];i=0
            while i<len(tw):
                if red[i]:
                    j=i
                    while j+1<len(tw) and red[j+1]: j+=1
                    a=tw[i][0];z=tw[j][1]
                    while a>0 and text[a-1] in "“‘«„\"'([": a-=1
                    while z<len(text) and text[z] in ".,;:!?’”»)…—'\"]": z+=1
                    # keep the span inside the quotation it belongs to
                    for lo,hi in marks[key]:
                        if lo<=tw[i][0]<hi: a=max(a,lo);z=min(z,hi) if hi<len(text) else z
                    spans.append((a,z));i=j+1
                else: i+=1
            marks[key]=spans
        nb=[]
        for ci,ch in enumerate(chs):
            nc=[]
            for vi,v in enumerate(ch):
                if (ci,vi) in marks:
                    text,_,_=wstruct.flat(v);items=[]
                    for lo,hi in marks[(ci,vi)]:
                        items.append((lo,1,{"r":1}));items.append((hi,0,{"r":0}))
                    v=insert_tokens(v,text,items)
                nc.append(v)
            nb.append(nc)
        out[b]=nb
    return out

def insert_tokens(toks,text,items):
    """Insert dict tokens at character offsets of the flat text. items: [(offset, order, dict)]."""
    items=sorted(items,key=lambda x:(x[0],x[1]))
    res=[];o=0;i=0
    for t in toks:
        if isinstance(t,str):
            cur=0
            while i<len(items) and (items[i][0]<o+len(t) or (items[i][0]==o+len(t) and items[i][2].get("r")==0)):
                cut=max(items[i][0]-o,cur)
                if t[cur:cut]: res.append(t[cur:cut])
                res.append(items[i][2]);cur=cut;i+=1
            if t[cur:]: res.append(t[cur:])
            o+=len(t)
        elif isinstance(t,list):
            if len(t)>=6 and o and text[o:o+1]==" ": o+=1
            while i<len(items) and items[i][0]<=o: res.append(items[i][2]);i+=1
            res.append(t);o+=len(t[0])
        else:
            if BREAK(t) and text[o:o+1]==" ": o+=1
            res.append(t)
    while i<len(items): res.append(items[i][2]);i+=1
    return res

# ---------- Greek texts ----------
def greek_red(books):
    out={}
    for b,chs in books.items():
        if b not in NT: out[b]=chs;continue
        nb=[]
        for ci,ch in enumerate(chs):
            nc=[]
            for vi,v in enumerate(ch):
                if not isinstance(v,list): nc.append(v);continue
                R,P=kjv_red_strongs((b,ci+1,vi+1))
                if not R: nc.append(v);continue
                idx=[i for i,t in enumerate(v) if isinstance(t,list) and len(t)>=6]
                st=[]
                for i in idx:
                    ss=set(x for x in v[i][1].split() if x)
                    st.append(True if ss&R and not ss&P else False if ss&P and not ss&R else None)
                # undecided words take the state of their neighbours
                for k in range(len(st)):
                    if st[k] is None:
                        l=next((st[j] for j in range(k-1,-1,-1) if st[j] is not None),None)
                        r=next((st[j] for j in range(k+1,len(st)) if st[j] is not None),None)
                        st[k]=(l and r) if (l is not None and r is not None) else bool(l if l is not None else r)
                # fill single-word gaps inside a red run
                for k in range(1,len(st)-1):
                    if not st[k] and st[k-1] and st[k+1]: st[k]=True
                res=[];on=False
                for i,t in enumerate(v):
                    if i in idx:
                        r=st[idx.index(i)]
                        if r and not on: res.append({"r":1});on=True
                        elif not r and on: res.append({"r":0});on=False
                    res.append(t)
                if on: res.append({"r":0})
                nc.append(res)
            nb.append(nc)
        out[b]=nb
    return out
