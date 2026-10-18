"""Add quotation marks to English versions that print none (KJV, ASV, Darby, ...)."""
import re
import align_en,wstruct
OPEN={0:"“",1:"‘",2:"“",3:"‘"};CLOSE={0:"”",1:"’",2:"”",3:"’"}
def red_gaps(toks,tw,text):
    out=[];o=0
    for t in toks:
        if isinstance(t,str): o+=len(t)
        elif isinstance(t,list):
            if len(t)>=6 and o and text[o:o+1]==" ": o+=1
            o+=len(t[0])
        elif isinstance(t,dict) and "r" in t:
            out.append((align_en.gap_of(tw,o),"o" if t["r"]==1 else "c"))
        elif isinstance(t,dict) and (t.get("p") or t.get("br") or t.get("d")==0 or ("l" in t and "h" not in t)):
            if text[o:o+1]==" ": o+=1
    return out
def plan_book(verses,sp,refs_of,snap_red=True):
    """verses: [(native_ref,tokens)]. Returns planned verses with mapped events [gap,kind,pid]."""
    import speech_alt
    tx={}
    for ref,toks in verses:
        for k in refs_of(ref): tx[k]=wstruct.flat(toks)[0]
    sp=speech_alt.apply(sp,tx.get)
    planned=[];ends={}
    for vi,(ref,toks) in enumerate(verses):
        text,br,spans=wstruct.flat(toks)
        tw=align_en.words(text);evs=[]
        info=[sp[k] for k in refs_of(ref) if k in sp]
        if len(info)==1 and not tw and info[0]["ev"]:
            # the version joins this verse to the one before: its closing marks go at the end of that verse
            pv=next((k for k in range(len(planned)-1,-1,-1) if planned[k]["tw"]),None)
            if pv is not None:
                for e in info[0]["ev"]:
                    if e[1]=="c":
                        planned[pv]["ev"].append([len(planned[pv]["tw"]),"c",e[3]]);ends.setdefault(e[3],{})["c"]=(pv,len(planned[pv]["tw"]))
        if len(info)==1 and tw and info[0]["ev"]:
            s=info[0]
            mapped,ratio,_=align_en.transfer(s["text"],[e[:3] for e in s["ev"]],text)
            if ratio<0.15:
                # weak alignment: keep only marks whose place does not depend on it (verse start / verse end)
                sw=align_en.words(s["text"])
                keepm=[(align_en.gap_of(sw,e[0])==0 and e[1]=="o") or (align_en.gap_of(sw,e[0])>=len(sw) and e[1]=="c") for e in s["ev"]]
                for (g,k,l),e,kp in zip(mapped,s["ev"],keepm):
                    if kp: evs.append([g,k,e[3]]);ends.setdefault(e[3],{})[k]=(vi,g)
            if ratio>=0.15:
                red=red_gaps(toks,tw,text) if snap_red else []
                others=[x[0] for x in mapped]
                for i_,((g,k,l),e) in enumerate(zip(mapped,s["ev"])):
                    def punct_at(x):
                        if x<=0 or x>=len(tw): return True
                        return re.search(r"[,:;.?!—]",text[tw[x-1][1]:tw[x][0]]) is not None
                    def crosses(a,b):     # another mark of this verse lies between the two places
                        lo_,hi_=min(a,b),max(a,b)
                        return any(lo_<=o_<=hi_ for j_,o_ in enumerate(others) if j_!=i_ and o_!=a)
                    near=[(abs(rg-g),rg) for rg,rk in red if l==0 and rk==k and abs(rg-g)<=6 and 0<rg<=len(tw) and punct_at(rg) and not crosses(g,rg)]
                    if near: g=min(near)[1]
                    evs.append([g,k,e[3]]);ends.setdefault(e[3],{})[k]=(vi,g)
        planned.append({"ref":ref,"text":text,"tw":tw,"ev":evs,"toks":toks})
    keep=set()
    closes={}
    for pid,e in ends.items():
        if "c" in e: closes.setdefault(e["c"][0],[]).append(e["c"][1])
    for pid,e in ends.items():
        if "o" not in e or "c" not in e: continue
        (ov,og),(cv,cg)=e["o"],e["c"]
        if (cv,cg)<=(ov,og): continue
        p=planned[ov];tw=p["tw"];text=p["text"]
        if 0<og<len(tw):
            between=text[tw[og-1][1]:tw[og][0]]
            short=cv==ov and cg-og<=4
            resumed=any(0<=og-x<=5 for x in closes.get(ov,[]))
            if not re.search(r"[,:;.?!—(\[]",between) and not short and not resumed: continue      # reads as indirect speech here
            resumed=any(0<=og-cg<=5 for cg in closes.get(ov,[]))   # ’ says Yahweh, ‘that …
            cap_that=text[tw[og][0]:tw[og][0]+4]=="That"      # the KJV marks a direct “That …” (ὅτι recitative) with a capital
            if tw[og][2]=="that" and ":" not in between and not resumed and not cap_that: continue
        keep.add(pid)
    for p in planned:
        p["ev"]=[e for e in p["ev"] if e[2] in keep]
        p["ev"].sort(key=lambda e:(e[0],0 if e[1]=="c" else 1))
    return planned
def crossing(seq):
    """seq: [(pid,kind)] in reading order. Pairs that do not nest properly (or lack an end)."""
    drop=set()
    while True:
        st=[];bad=None
        for pid,k in seq:
            if pid in drop: continue
            if k=="o": st.append(pid)
            elif pid in st:
                if st[-1]!=pid: bad=st[-1];break
                st.pop()
            else: bad=pid;break
        if bad is None:
            drop|=set(st);return drop
        drop.add(bad)
def realize(planned,para_start):
    seq=[(e[2],e[1]) for p in planned for e in p["ev"]]
    drop=crossing(seq)
    for p in planned: p["ev"]=[e for e in p["ev"] if e[2] not in drop]
    out=[];stack=[]
    for vi,p in enumerate(planned):
        toks=p["toks"];text=p["text"];tw=p["tw"];marks=[]
        if stack and para_start(vi) and tw:
            off=tw[0][0]
            while off>0 and text[off-1] in "[(": off-=1
            for lvl in range(len(stack)): marks.append((off,OPEN[lvl%4],{"ro":1,"pid":stack[lvl]}))
        for g,k,pid in p["ev"]:
            if k=="o":
                lvl=len(stack);stack.append(pid)
                off=tw[g][0] if g<len(tw) else len(text.rstrip())
                while off>0 and text[off-1] in "[(": off-=1
                marks.append((off,OPEN[lvl%4],{"pid":pid}))
            else:
                if pid not in stack: continue
                while stack and stack[-1]!=pid: stack.pop()
                lvl=len(stack)-1;stack.pop()
                off=align_en.insertion_offset(text,tw,g,"c")
                while off<len(text) and text[off] in "].,!?": off+=1
                marks.append((off,CLOSE[lvl%4],{"pid":pid}))
        out.append(apply_marks(toks,text,marks))
    return out
def Q(m):
    d={"q":m[1],"a":1}
    if len(m)>2: d.update(m[2])
    return d
def apply_marks(toks,text,marks):
    if not marks: return toks
    marks=[m for _,m in sorted(enumerate(marks),key=lambda x:(x[1][0],x[0]))]
    res=[];o=0;mi=0
    for t in toks:
        if isinstance(t,str):
            s=t;start=o;cur=0
            while mi<len(marks) and (marks[mi][0]<start+len(s) or (marks[mi][0]==start+len(s) and marks[mi][1] in "”’")):
                cut=max(marks[mi][0]-start,cur)
                if s[cur:cut]: res.append(s[cur:cut])
                res.append(Q(marks[mi]));cur=cut;mi+=1
            if s[cur:]: res.append(s[cur:])
            o+=len(s)
        elif isinstance(t,list):
            if len(t)>=6 and o and text[o:o+1]==" ": o+=1
            L=len(t[0])
            while mi<len(marks) and marks[mi][0]<=o: res.append(Q(marks[mi]));mi+=1
            # marks that fall inside a multi-word tagged phrase split the phrase (both parts keep the tag)
            cur=0
            while mi<len(marks) and o<marks[mi][0]<o+L:
                cut=marks[mi][0]-o
                piece=t[0][cur:cut]
                if piece: res.append([piece]+list(t[1:]))
                res.append(Q(marks[mi]));cur=cut;mi+=1
            rest=t[0][cur:]
            if rest: res.append([rest]+list(t[1:]) if cur else t)
            o+=L
            while mi<len(marks) and marks[mi][0]<=o and marks[mi][1] in "”’": res.append(Q(marks[mi]));mi+=1
        else:
            if isinstance(t,dict) and (t.get("p") or t.get("br") or t.get("d")==0 or ("l" in t and "h" not in t)) and text[o:o+1]==" ": o+=1
            res.append(t)
    while mi<len(marks): res.append(Q(marks[mi]));mi+=1
    return res
