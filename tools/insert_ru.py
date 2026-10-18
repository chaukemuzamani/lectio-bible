"""Add quotation marks to the Russian / Church Slavonic versions.

The speech events placed in the KJV (see insert_en) are carried across through Strong's numbers:
each KJV word has its Strong's tags, and the Russian words are aligned to Strong's numbers by the
statistical table in data/align. A mark is then snapped to a place where Russian punctuation allows
it — an opening mark after a colon (or at the start of a verse), a closing mark before punctuation.
Pairs that cannot be placed with confidence are left out entirely.

Russian typography: «outer „inner“ outer», capital letter after the opening mark, a full stop or
comma after the closing mark (?, ! and … stay inside)."""
import sys,os,re,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import insert_en,wstruct,align_en,sources,strongs_align as sa
from vrs import to_kjv,PROT
OPEN={0:"«",1:"„",2:"«",3:"„"};CLOSE={0:"»",1:"“",2:"»",3:"“"}
WIN=6

def kjv_plan(sp):
    """{kjv ref: {"tw":words,"st":[set of strongs per word],"ev":[[gap,kind,pid]],"n":len}}"""
    K=sources.load_base("KJVS");out={}
    for b in K:
        verses=[((b,ci+1,vi+1),v) for ci,ch in enumerate(K[b]) for vi,v in enumerate(ch)]
        plan=insert_en.plan_book(verses,sp,lambda r:[r],snap_red=True)
        for (ref,toks),p in zip(verses,plan):
            text,_,spans=wstruct.flat(toks)
            st=[]
            for (a,e,_w) in p["tw"]:
                tok=next((toks[i] for s0,e0,i in spans if s0<=a<e0),None)
                st.append(set(tok[1].split()) if isinstance(tok,list) and len(tok)>1 and tok[1] else set())
            red=red_words(toks,p["tw"],text)
            out[ref]={"tw":p["tw"],"st":st,"ev":p["ev"],"red":red,"text":p["text"]}
    return out

def red_words(toks,tw,text):
    """Indices of KJV words printed in red."""
    on=False;o=0;marks=[]
    for t in toks:
        if isinstance(t,str): o+=len(t)
        elif isinstance(t,list):
            if len(t)>=6 and o and text[o:o+1]==" ": o+=1
            o+=len(t[0])
        elif isinstance(t,dict):
            if "r" in t: marks.append((o,t["r"]))
            elif (t.get("p") or t.get("br") or t.get("d")==0 or ("l" in t and "h" not in t)) and text[o:o+1]==" ": o+=1
    out=set()
    for i,(a,e,_w) in enumerate(tw):
        st=False
        for off,r in marks:
            if off<=a: st=bool(r)
        if st: out.add(i)
    return out

def components(book,nverses,vc):
    """Group target verses and KJV verses into units connected by the versification map."""
    units=[];cur=None;seen_k={}
    for c,nv in enumerate(nverses,1):
        for v in range(1,nv+1):
            ks=to_kjv(vc,book,c,v) if book in PROT else []
            ks=[k for k in ks if k[0]==book]
            join=cur is not None and any(k in cur["k"] for k in ks)
            if not join:
                cur={"t":[],"k":[]};units.append(cur)
            cur["t"].append((c,v))
            for k in ks:
                if k not in cur["k"]: cur["k"].append(k)
    return units

def lis_anchors(KW,TS):
    """Monotone correspondences between KJV phrases and target words through shared Strong's numbers.
    A phrase is a run of KJV words carrying the same tags (one tagged token, e.g. “for us? Then said I”).
    Returns [(first_kjv_word, last_kjv_word, target_index)]."""
    ph=[]
    for k,st in enumerate(KW):
        if st and ph and ph[-1][2]==st and ph[-1][1]==k-1: ph[-1][1]=k
        elif st: ph.append([k,k,st])
    pairs=[(i,t) for i,(_a,_b,st) in enumerate(ph) for t,s in enumerate(TS) if s and (s&st)]
    if not pairs: return []
    best=[1]*len(pairs);prev=[-1]*len(pairs)
    for i in range(len(pairs)):
        for j in range(i):
            if pairs[j][0]<pairs[i][0] and pairs[j][1]<pairs[i][1] and best[j]+1>best[i]: best[i]=best[j]+1;prev[i]=j
    i=max(range(len(pairs)),key=lambda x:best[x]);out=[]
    while i>=0: out.append((ph[pairs[i][0]][0],ph[pairs[i][0]][1],pairs[i][1]));i=prev[i]
    return out[::-1]

DROP=-3.5
SPEECH_RU=re.compile(r"(?i)(сказ|говор|рек|рёк|рече|глаго|отвеч|отвѣч|спрос|вопро|воскл|взыв|возопи|молил|пове|кричал|вопия|отвѣт|ответ|сказа)")
def assign(evs):
    """Choose one place per event (or none) keeping the KJV order, maximising the total score."""
    m=len(evs)
    if not m: return []
    # state: (event index, chosen position) ; dp over events in order
    import math
    states=[{}]   # list per event: pos -> (score, back)
    prev={None:(0.0,None)}   # last chosen position (None = nothing chosen yet) -> (score, path)
    for i,(g,kind,pid,kref,cands) in enumerate(evs):
        nxt={}
        for lp,(sc,path) in prev.items():
            # drop this event
            k=lp
            v=(sc+DROP,path)
            if k not in nxt or v[0]>nxt[k][0]: nxt[k]=v
            for p,c in cands:
                if lp is not None:
                    lpos,lkind,lg,lpid=lp
                    if p<lpos: continue
                    if p==lpos and kind=="o" and lkind=="o" and g-lg>=2: continue
                    if p==lpos and kind=="c" and lkind=="o" and lpid==pid: continue
                    if p==lpos and kind=="o" and lkind=="c" and g-lg>=2 and False: continue
                key=(p,kind,g,pid)
                v=(sc+c,path+((i,p),) if path else ((i,p),))
                if key not in nxt or v[0]>nxt[key][0]: nxt[key]=v
        prev=nxt
    sc,path=max(prev.values(),key=lambda x:x[0])
    return [(evs[i][0],evs[i][1],evs[i][2],evs[i][3],p) for i,p in (path or ())]

def intro_first(text):
    """The verse opens with a speech introduction (“И сказал Господь: …”)."""
    m=re.match(r"([^:.;!?«»]*):",text)
    return bool(m and len(m.group(1).split())<=10 and SPEECH_RU.search(m.group(1)))
def intro_before_colon(text,end):
    """The clause that ends at `end` (just before a colon) introduces speech."""
    start=max(text.rfind(c,0,end) for c in ".;!?«»:")+1
    return bool(SPEECH_RU.search(text[start:end]))
def tgt_words(text,lang):
    return [(m.start(),m.end(),m.group(0)) for m in sa.WORDRE[lang].finditer(text)]

def plan_version(code,books,vc,lang,KP,hints=None):
    """Returns {book: [[(text_offset_events) per verse]]} as planned marks per target verse."""
    result={}
    for b,chs in books.items():
        if b not in PROT: continue
        vcb=vc.get(b,"kjv") if isinstance(vc,dict) else vc
        units=components(b,[len(ch) for ch in chs],vcb)
        # per target verse: flat text, words, strongs per word
        info={}
        ends={}
        for ui,u in enumerate(units):
            # target words (global within the unit)
            TW=[];vstart={}
            for (c,v) in u["t"]:
                toks=chs[c-1][v-1];text,_,_=wstruct.flat(toks)
                ws=tgt_words(text,lang);S=set()
                for k in to_kjv(vcb,b,c,v): S|=sa.ref_strongs(*k)
                al=sa.align_words(code,[w[2] for w in ws],S) if ws else {}
                cs=sa.candidates(code,[w[2] for w in ws],S) if ws else []
                vstart[(c,v)]=len(TW)
                info[(c,v)]={"text":text,"ws":ws,"g0":len(TW),"ev":[]}
                for i,w in enumerate(ws): TW.append(((c,v),i,al.get(i),text,w,cs[i]|({al[i]} if i in al else set())))
            if not TW: continue
            # KJV words of the unit
            KW=[];KE=[]
            for k in u["k"]:
                p=KP.get(k)
                if not p: continue
                base=len(KW)
                for i,st in enumerate(p["st"]): KW.append(st)
                for g,kind,pid in p["ev"]:
                    pk=""
                    if kind=="c" and g>0:
                        m=re.match(r"[\])]*\s*([?!.;,:])",p["text"][p["tw"][g-1][1]:])
                        pk=m.group(1) if m else ""
                    KE.append((base+g,kind,pid,k,g==len(p["tw"]),pk))
            if not KE: continue
            n=len(TW)
            anc=lis_anchors(KW,[w[5] for w in TW])
            def between(gi):
                ref,i,_,text,w,_c=TW[gi]
                if i==0: return text[:w[0]],True
                return text[TW[gi-1][4][1]:w[0]],False
            def after_text(gi):
                ref,i,_,text,w,_c=TW[gi-1];return text[w[1]:]
            def ends_verse(gi): return gi>=n or TW[gi][1]==0
            evs=[]
            for (g,kind,pid,kref,at_end,kp) in KE:
                Ls=[x for x in anc if x[1]<g];Rs=[x for x in anc if x[0]>=g]
                L=Ls[-1] if Ls else None;R=Rs[0] if Rs else None
                lo=L[2]+1 if L else 0
                hi=R[2] if R else n
                if hi<lo: lo,hi=hi,lo
                kl=L[1]+1 if L else 0;kr=R[0] if R else len(KW)
                frac=(g-kl)/max(kr-kl,1)
                est=lo+frac*(hi-lo)
                if kind=="o" and R and R[0]==g: est=hi
                if kind=="c" and L and L[1]==g-1: est=lo
                cands=[]
                for p in range(0,n+1):
                    d=abs(p-est)
                    if d>WIN: continue
                    out_rng=0 if lo-1<=p<=hi+1 else min(abs(p-lo),abs(p-hi))
                    if kind=="o":
                        if p>=n: continue
                        btw,vs=between(p)
                        if not (vs or ":" in btw or "—" in btw): continue
                        if vs and intro_first(TW[p][3]): continue
                        sc=-(0.3*d if not out_rng else 0.6*d+1.5*out_rng)+(1.5 if ":" in btw else 0)
                        if g<len(KW) and TW[p][2] and TW[p][2] in KW[g]: sc+=1.5
                    else:
                        if p==0: continue
                        aft=after_text(p);ve=ends_verse(p)
                        if not (re.match(r"\s*[.,;:!?…—)]",aft) or ve): continue
                        sc=-(0.3*d if not out_rng else 0.6*d+1.5*out_rng)+(1 if re.match(r"\s*[.;!?…]",aft) or ve else 0)
                        if re.match(r"\s*:",aft) and intro_before_colon(TW[p-1][3],TW[p-1][4][1]): sc-=4     # «… И я сказал»: — the colon introduces the next speech
                        if g>0 and TW[p-1][2] and TW[p-1][2] in KW[g-1]: sc+=1.5
                        m=re.match(r"\s*([?!.;,:])",aft)
                        if m and kp and m.group(1)==kp: sc+=2 if kp in "?!" else 0.5
                        if at_end and ve and TW[p-1][0]==TW[min(p,n)-1][0]: sc+=2
                    if hints:
                        key=(b,)+TW[p][0]+(TW[p][1],) if kind=="o" else (b,)+TW[p-1][0]+(TW[p-1][1]+1,)
                        if key in hints: sc+=4
                    cands.append((p,sc))
                evs.append((g,kind,pid,kref,cands))
            chosen=assign(evs)
            # a quotation must hold the words of the KJV quotation, not those around it
            span={}
            for (g,kind,pid,kref,p) in chosen: span.setdefault(pid,{})[kind]=(g,p)
            bad=set()
            for pid,e in span.items():
                go,po=e.get("o",(0,0));gc,pc=e.get("c",(len(KW),n))
                if "o" not in e and "c" not in e: continue
                inside=set().union(*KW[go:gc]) if gc>go else set()
                outside=set().union(*(KW[:go]+KW[gc:])) if KW else set()
                hin=hout=0
                for w in TW[po:pc]:
                    c_=w[5]
                    if not c_: continue
                    if c_&inside: hin+=1
                    elif c_&outside: hout+=1
                if hout>=hin and hout>=1: bad.add(pid)
            for (g,kind,pid,kref,p) in chosen:
                if pid in bad: continue
                if kind=="o": ref=TW[p][0];wi=TW[p][1]
                else: ref=TW[p-1][0];wi=TW[p-1][1]+1
                info[ref]["ev"].append([wi,kind,pid,g,kref])
                ends.setdefault(pid,{})[kind]=(ref,wi)
        # keep pairs whose two ends were placed, in order
        order={}
        for ci,ch in enumerate(chs):
            for vi,_ in enumerate(ch): order[(ci+1,vi+1)]=len(order)
        keep=set()
        for pid,e in ends.items():
            if "o" in e and "c" in e and (order[e["o"][0]],e["o"][1])<(order[e["c"][0]],e["c"][1]): keep.add(pid)
        # inside a verse the marks must keep the KJV order
        changed=True
        while changed:
            changed=False
            for ref,d in info.items():
                ev=[x for x in d["ev"] if x[2] in keep]
                ev.sort(key=lambda x:(x[4],x[3],0 if x[1]=="c" else 1))
                for a,bb in zip(ev,ev[1:]):
                    if bb[0]<a[0]:
                        keep.discard(bb[2]);changed=True;break
        out=[]
        for ci,ch in enumerate(chs):
            row=[]
            for vi,_ in enumerate(ch):
                d=info.get((ci+1,vi+1))
                ev=[] if not d else sorted([x for x in d["ev"] if x[2] in keep],key=lambda x:(x[0],0 if x[1]=="c" else 1,x[4],x[3]))
                row.append({"text":d["text"] if d else "","ws":d["ws"] if d else [],"ev":ev})
            out.append(row)
        result[b]=out
    return result

def realize(chs,plan,para_start):
    """Insert the marks into the token lists of one book."""
    if plan:
        drop=insert_en.crossing([(e[2],e[1]) for row in plan for p in row for e in p["ev"]])
        for row in plan:
            for p in row: p["ev"]=[e for e in p["ev"] if e[2] not in drop]
    stack=[];res=[]
    for ci,ch in enumerate(chs):
        row=[]
        for vi,toks in enumerate(ch):
            p=plan[ci][vi] if plan else {"text":"","ws":[],"ev":[]}
            text=p["text"];ws=p["ws"];marks=[]
            if stack and ws and para_start(ci+1,vi+1):
                for lvl in range(len(stack)): marks.append((ws[0][0],OPEN[lvl%4],{"ro":1,"pid":stack[lvl]}))
            for wi,kind,pid,_g,_k in p["ev"]:
                if kind=="o":
                    lvl=len(stack);stack.append(pid)
                    off=ws[wi][0] if wi<len(ws) else len(text.rstrip())
                    marks.append((off,OPEN[lvl%4],{"pid":pid}))
                else:
                    if pid not in stack: continue
                    while stack and stack[-1]!=pid: stack.pop()
                    lvl=len(stack)-1;stack.pop()
                    off=ws[wi-1][1]
                    m=re.match(r"[?!…]+",text[off:])
                    if m: off+=m.end()
                    marks.append((off,CLOSE[lvl%4],{"pid":pid}))
            new=insert_en.apply_marks(toks,text,marks)
            row.append(capitalize(new))
        res.append(row)
    return res

def capitalize(toks):
    out=list(toks)
    for i,t in enumerate(out):
        if isinstance(t,dict) and t.get("q") in ("«","„") and not t.get("ro"):
            for j in range(i+1,len(out)):
                u=out[j]
                if isinstance(u,str):
                    m=re.search(r"\S",u)
                    if not m: continue
                    if u[m.start()].islower(): out[j]=u[:m.start()]+u[m.start()].upper()+u[m.start()+1:]
                    break
                if isinstance(u,dict) and "q" in u: continue
                break
    return out

def strip_own(books):
    """Remove the version's own straight quotation marks; remember where they were as hints."""
    hints=set()
    for b,chs in books.items():
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                if not any(isinstance(t,str) and '"' in t for t in v): continue
                text,_,_=wstruct.flat(v)
                ws=tgt_words(text,"ru")
                for m in re.finditer('"',text):
                    o=m.start()
                    nxt=next((i for i,w in enumerate(ws) if w[0]>=o),len(ws))
                    hints.add((b,ci+1,vi+1,nxt))
                ch[vi]=[t.replace('"',"") if isinstance(t,str) else t for t in v]
    return hints
