"""Word alignment between two English texts of the same verse, used to carry quotation
marks, red letters and paragraph breaks across versions."""
import re,difflib
WORD=re.compile(r"[A-Za-z]+(?:[’'][A-Za-z]+)*")
ARCH={"thee":"you","thou":"you","ye":"you","thy":"your","thine":"your","hath":"has","doth":"does","art":"are",
 "shalt":"shall","wilt":"will","canst":"can","hast":"have","dost":"do","didst":"did","saith":"say","spake":"speak",
 "unto":"to","upon":"on","jehovah":"lord","yahweh":"lord","yhwh":"lord","jesus":"jesus","yeshua":"jesus","iesus":"jesus",
 "vnto":"to","vpon":"on","sayd":"said","saide":"said","sayde":"said","sayeth":"says","sayth":"says","god":"god",
 "behold":"behold","lo":"behold","verily":"truly","amen":"truly","whosoever":"whoever","whatsoever":"whatever",
 "begotten":"begotten","heaven":"heaven","heavens":"heaven","shew":"show","shewed":"showed","answered":"answered"}
IRREG={"said":"say","says":"say","saith":"say","saying":"say","sayd":"say","saide":"say","sayde":"say","sayeth":"say","sayth":"say",
 "spake":"speak","spoke":"speak","spoken":"speak","came":"come","cometh":"come","went":"go","goeth":"go","gone":"go","saw":"see","seen":"see",
 "knew":"know","known":"know","took":"take","taken":"take","gave":"give","given":"give","made":"make","brought":"bring","sent":"send",
 "told":"tell","heard":"hear","found":"find","began":"begin","stood":"stand","sat":"sit","ate":"eat","eaten":"eat","drank":"drink",
 "wrote":"write","written":"write","answered":"answer","answering":"answer","answereth":"answer","asked":"ask","cried":"cry","crieth":"cry",
 "am":"be","is":"be","are":"be","was":"be","were":"be","art":"be","been":"be","hath":"have","has":"have","had":"have","hast":"have",
 "doth":"do","does":"do","did":"do","dost":"do","didst":"do","shalt":"shall","wilt":"will","canst":"can","couldest":"could","shouldest":"should","wouldest":"would"}
def emod(w):
    """Spelling key that lets early-modern spellings (Geneva, Tyndale) meet modern ones."""
    if w.startswith(("vn","vp")) or w=="vs": w="u"+w[1:]
    w=re.sub(r"(?<=[aeiou])u(?=[aeiou])","v",w)
    if len(w)>2 and re.match(r"i[aeou]",w): w="j"+w[1:]
    w=re.sub(r"(.)\1",r"\1",w)
    if len(w)>3 and w.endswith("e"): w=w[:-1]
    return w
def norm(w): return emod(_norm(w))
def _norm(w):
    w=w.lower().replace("’","'")
    if w.startswith(("vn","vp")) or w=="vs": w="u"+w[1:]
    w=re.sub(r"'s$","",w)
    w=ARCH.get(w,w)
    if w in IRREG: return IRREG[w]
    for suf in ("eth","est","ing","ed","es","s"):
        if (len(w)>4 or (suf=="s" and len(w)>3 and not w.endswith("ss"))) and w.endswith(suf):
            r=w[:-len(suf)]
            return IRREG.get(r,r)
    return w
def words(text):
    return [(m.start(),m.end(),norm(m.group(0))) for m in WORD.finditer(text)]
SPEECH={norm(w) for w in "said says say saying sayd answered answering asked replied cried cry spoke spake told tell wrote written commanded called declared prayed sware swore swear sang sing proclaimed thus".split()}
VERBS=r"said|saith|sayth|sayd|saide|sayde|says|saying|answered|answering|answereth|asked|replied|cried|crieth|spake|spoke|commanded|called"
def fix_intro(tgt,tw,g):
    """An opening mark must not sit in front of “and said,” — move it past such an introduction."""
    if g>=len(tw): return g
    for j in range(g+1,min(len(tw),g+8)+1):
        seg=tgt[tw[g][0]:tw[j][0] if j<len(tw) else len(tgt)]
        if re.search(r"[.?!;]",seg): break
        if re.match(r"^\W*((and|then|but)\s+)?("+VERBS+r")\b[^,:]*[,:]\s*$",seg,re.I) and len(seg.split())<=7: return j
    return g
def anchors(sw,tw):
    a=[x[2] for x in sw];b=[x[2] for x in tw]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    m={}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): m[blk.a+k]=blk.b+k
    return m,sm.ratio()
def gap_of(words_,off):
    """Number of words that start before char offset `off`."""
    return sum(1 for w in words_ if w[0]<off)
def map_gap(g,m,ns,nt):
    """Target gap range for source gap g, and the gap's relative position between its anchors."""
    L=max([i for i in m if i<g],default=None);R=min([i for i in m if i>=g],default=None)
    lo=m[L]+1 if L is not None else 0
    hi=m[R] if R is not None else nt
    if R is None and L is None: lo=hi=round(g*nt/max(ns,1))
    sl=(L+1) if L is not None else 0;sr=R if R is not None else ns
    frac=(g-sl)/max(sr-sl,1) if sr>sl else 0.0
    return lo,max(lo,hi),frac
def choose(tgt,tw,lo,hi,kind,frac):
    """Pick a target gap in [lo,hi] for an opening ('o') or closing ('c') mark."""
    if lo==hi: return lo
    best=None
    for g in range(lo,hi+1):
        # text between previous word end and next word start
        pe=tw[g-1][1] if g>0 else 0
        ns=tw[g][0] if g<len(tw) else len(tgt)
        between=tgt[pe:ns]
        prevw=tw[g-1][2] if g>0 else ""
        score=0
        if kind=="o":
            if g<len(tw) and intro_word(tgt,tw[g]): score-=5     # never open right before "saying"
            if re.search(r"[,:;]",between): score+=2
            if prevw in SPEECH or INTRO_END.search(tgt[max(0,pe-30):pe]): score+=3
            if g<len(tw) and tgt[tw[g][0]:tw[g][0]+1].isupper(): score+=1
            if re.search(r"[.?!]",between): score+=1
        else:
            if re.search(r"[.?!]",between): score+=3
            elif re.search(r"[,;:(]",between): score+=2
            if g<len(tw) and tw[g][2] in SPEECH: score+=1
        pos=(g-lo)/max(hi-lo,1)
        score-=abs(pos-frac)*1.5
        if best is None or score>best[0]: best=(score,g)
    return best[1]
def insertion_offset(tgt,tw,g,kind):
    """Character offset for a mark at word gap g."""
    if kind=="o":
        return tw[g][0] if g<len(tw) else len(tgt.rstrip())
    if g==0: return 0
    e=tw[g-1][1]
    while e<len(tgt) and tgt[e] in ".,!?": e+=1
    return e

INTRO_END=re.compile(r"\b(said|saith|sayth|says|say|saying|sayd|saide|sayde|answered|answering|answereth|cried|crieth|spake|spoke|speaketh|asked|replied|told|commanded|commandeth|wrote|written|thus|exclaimed|called|calleth|prayed|sware|swore|sang|declared|charged|warned|shouted|whispered|confessed)(\s+(unto|to|vnto|of|concerning|before|again|aloud|with)?\s*(him|her|them|me|us|you|thee|it|his\s+\w+|the\s+\w+|\w+))?\W*$",re.I)
SPEECHNEAR=re.compile(r"\b(said|saith|sayth|says|saying|answered|answereth|cried|spake|spoke|asked|replied|commanded|charged|called|prayed)\b[^.?!;:,]{0,40}$",re.I)
PAST=set("said saith sayth sayd saide sayde says saying sayeth answered answering answereth spake spoke spoken speaking speaketh cried crying crieth".split())
def intro_word(tgt,w):
    """True for “saying”, “said”, “answered” … — words that introduce speech rather than begin it.
    An imperative at the start of speech (“Speak unto Aaron”, “Say ye”) does not count."""
    if w[2] not in ("say","answer","speak","cry"): return False
    raw=tgt[w[0]:w[1]]
    return raw[:1].islower() or raw.lower() in PAST
def snap_open(tgt,tw,g,radius=2):
    """Move an opening quote to a nearby position right after a speech introduction ("said," / ":")."""
    best=None
    for d in range(-radius,radius+1):
        h=g+d
        if h<0 or h>len(tw): continue
        pe=tw[h-1][1] if h>0 else 0
        ns=tw[h][0] if h<len(tw) else len(tgt)
        between=tgt[pe:ns]
        before=tgt[max(0,pe-25):pe]
        s=0
        if h<len(tw) and intro_word(tgt,tw[h]): continue
        if re.search(r"[,:]",between) and (INTRO_END.search(before) or SPEECHNEAR.search(tgt[max(0,pe-45):pe]) or ":" in between): s=3
        elif h==0 and not (tw and intro_word(tgt,tw[0])): s=1 if d==0 else 0
        if s and (best is None or (s,-abs(d))>best[0]): best=((s,-abs(d)),h)
    return best[1] if best else g
def snap_close(tgt,tw,g,radius=2):
    best=None
    for d in range(-radius,radius+1):
        h=g+d
        if h<1 or h>len(tw): continue
        pe=tw[h-1][1]
        ns=tw[h][0] if h<len(tw) else len(tgt)
        between=tgt[pe:ns]
        s=0
        if h==len(tw): s=2
        if re.search(r"[.?!]",between): s=3
        elif re.search(r"[;:]",between): s=2
        elif re.search(r",",between): s=1
        if s and (best is None or (s,-abs(d))>best[0]): best=((s,-abs(d)),h)
    return best[1] if best else g
def transfer(stext,sev,ttext,snap=True):
    """Map quote events from a source verse onto a target verse.
    sev: [(offset,kind,level)] with kind o/c/r. Returns [(target_gap,kind,level)] and alignment ratio."""
    sw=words(stext);tw=words(ttext)
    m,ratio=anchors(sw,tw)
    out=[];raw=[]
    for o,k,l in sev:
        if k not in ("o","c","r"): continue
        g=gap_of(sw,o)
        if g==0 and k in ("o","r"):
            first=" ".join(w[2] for w in sw[:4])
            t=snap_open(ttext,tw,0,radius=3) if snap and not re.search(r"\b(says|saith|said|say|speaks)\b",first) else 0
            if snap: t=fix_intro(ttext,tw,t)
            out.append((t,k,l));raw.append(t);continue
        if g>=len(sw) and k=="c": out.append((len(tw),k,l));raw.append(len(tw));continue
        lo,hi,frac=map_gap(g,m,len(sw),len(tw))
        t=choose(ttext,tw,lo,hi,"o" if k in ("o","r") else "c",frac);raw.append(t)
        if snap:
            if hi>lo:      # pinned between two matched words: leave it there
                t=snap_open(ttext,tw,t) if k in ("o","r") else snap_close(ttext,tw,t)
            if k in ("o","r"): t=fix_intro(ttext,tw,t)
        out.append((t,k,l))
    # two opening marks that land together although words separate them in the source:
    # keep the outer one where the alignment first put it
    for i in range(len(out)-1):
        a,b=out[i],out[i+1]
        if a[1]=="o" and b[1]=="o" and a[0]==b[0] and raw[i]<a[0]: out[i]=(raw[i],a[1],a[2])
    return out,ratio,tw
