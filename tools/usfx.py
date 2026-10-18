"""Parse USFX (eBible XML) into per-verse token lists with structure.

Token vocabulary (shared with the reader):
  "text"                         plain text
  {"f": note}                    footnote
  {"p": 1}                       paragraph / stanza start
  {"l": 1|2}                     poetry line start (indent level)
  {"r": 1} / {"r": 0}            words of Jesus start / end
  {"d": 1} / {"d": 0}            psalm superscription start / end
  {"h": text, "l": n, "x": refs} heading (n: 0 major, 1 section, 2 sub-section, 3 speaker, 4 acrostic)
"""
import re
from vrs import USFM,PROT
SKIP={"toc","id","ide","rem","h","cl","cp","x","fr","languageCode","vp","ca","va","fig"}
INTRO={"mt","mt1","mt2","mt3","ip","is","is1","imt","imt1","ili","ili1","mte","mte1","toc","io","io1","iot"}
SPECIAL={"r":None,"mr":0,"ms":0,"ms1":0,"ms2":0,"qa":4,"sp":3,"s":1,"s1":1,"s2":2,"s3":2,"d":"d"}
TOK=re.compile(r"<(/?)([\w:]+)((?:\s+[\w:-]+=\"[^\"]*\")*)\s*(/?)>|([^<]+)",re.S)
def attr(a,k):
    m=re.search(r'\b'+k+r'="([^"]*)"',a or "");return m.group(1) if m else None
def clean(t): return re.sub(r"\s+"," ",t).strip()
def parse(path,keep_lines=True):
    s=open(path,encoding="utf-8").read()
    books={};cur=None;c=0;v=0;inv=False
    stack=[];pst=[]           # element stack; paragraph-style stack
    pend=[]                   # structure waiting for the next verse
    fn=None;cap=None;lvl_s=1  # footnote buffer; captured special block
    def where(): return books[cur][c-1][v-1] if inv else pend
    def put(x):
        if cur is None or c==0: return
        where().append(x)
    def text(t):
        if fn is not None:
            if stack and stack[-1] in ("fr","fv"): return
            fn.append(t);return
        if cap is not None: cap["buf"].append(t);return
        if any(x in SKIP for x in stack): return
        if pst and pst[-1] in INTRO: return
        if cur is None or c==0: return
        if not inv and not t.strip(): return
        put(t)
    for m in TOK.finditer(s):
        close,tag,attrs,selfc,tx=m.groups()
        if tx is not None: text(tx);continue
        if tag=="book" and not close:
            bid=attr(attrs,"id");cur=PROT[USFM.index(bid)] if bid in USFM else None
            if cur: books[cur]=[]
            c=v=0;pend=[];inv=False;continue
        if tag=="c" and not close and cur:
            c=int(re.match(r"\d+",attr(attrs,"id")).group(0));v=0;inv=False
            while len(books[cur])<c: books[cur].append([])
            continue
        if tag=="v" and not close and cur and c:
            v=int(re.match(r"\d+",attr(attrs,"id")).group(0));inv=True
            ch=books[cur][c-1]
            while len(ch)<v: ch.append([])
            if pend: ch[v-1].extend(pend);pend=[]
            continue
        if tag=="ve": inv=False;continue
        if selfc:
            if tag=="b" and cur and c: put({"p":1})
            continue
        if not close:
            stack.append(tag)
            if tag=="f": fn=[]
            elif tag=="wj": put({"r":1})
            elif tag=="s":
                st=attr(attrs,"style") or "s1";lv=attr(attrs,"level")
                cap={"kind":"s","l":int(lv) if lv else SPECIAL.get(st,1),"buf":[]};lvl_s=cap["l"]
            elif tag=="d": cap={"kind":"d","buf":[]}
            elif tag=="p":
                st=attr(attrs,"style") or attr(attrs,"sfm") or "p";pst.append(st)
                if st in SPECIAL and st not in ("s","s1","s2","s3"): cap={"kind":st,"buf":[]}
                elif st not in INTRO and cur and c: put({"p":1})
            elif tag=="q":
                if keep_lines and cur and c: put({"l":int(attr(attrs,"level") or 1)})
            continue
        # closing tags
        if tag=="f" and fn is not None:
            t=clean("".join(fn));fn=None
            if t: put({"f":t})
        elif tag=="wj": put({"r":0})
        elif tag in ("s","d","p") and cap is not None and (tag!="p" or (pst and pst[-1]==cap["kind"])):
            t=clean("".join(cap["buf"]));k=cap["kind"];cap=None
            if t:
                if k=="s": put({"h":t,"l":lvl_s})
                elif k=="d":
                    if re.fullmatch(r"[A-Z]{2,8}\.?",t): put({"h":t,"l":4})
                    else:
                        put({"d":1});put(t);put({"d":0})
                elif k=="r":
                    tgt=where()
                    for x in reversed(tgt):
                        if isinstance(x,dict) and "h" in x: x["x"]=t;break
                elif k=="mr":
                    tgt=where()
                    for x in reversed(tgt):
                        if isinstance(x,dict) and x.get("l")==0: x["x"]=t;break
                    else: put({"h":t,"l":0})
                else: put({"h":t,"l":SPECIAL[k]})
        if tag=="p" and pst: pst.pop()
        if stack and stack[-1]==tag: stack.pop()
        elif tag in stack:
            while stack and stack[-1]!=tag: stack.pop()
            if stack: stack.pop()
    return {b:[[tidy(vs) for vs in ch] for ch in chs] for b,chs in books.items()}
_last_s=[1]
def _lv(t,k,attrs): return _last_s[0]
def tidy(toks):
    out=[]
    for t in toks:
        if isinstance(t,str):
            t=re.sub(r"\s+"," ",t)
            if out and isinstance(out[-1],str): out[-1]+=t
            else: out.append(t)
        else: out.append(t)
    STRUCT=lambda x:isinstance(x,dict) and (x.get("p") or "l" in x and "h" not in x or "h" in x or x.get("d") is not None)
    for i,t in enumerate(out):
        if not isinstance(t,str): continue
        j=i-1
        while j>=0 and isinstance(out[j],dict) and ("f" in out[j] or "r" in out[j]): j-=1
        if j<0 or STRUCT(out[j]): t=t.lstrip()
        k=i+1
        while k<len(out) and isinstance(out[k],dict) and ("f" in out[k] or "r" in out[k]): k+=1
        if k>=len(out) or STRUCT(out[k]): t=t.rstrip()
        out[i]=t
    out=[t for t in out if t!=""]
    if any(isinstance(t,str) and (t!=t.strip()) for t in out) and len(out)>0:
        pass
    # second pass: whitespace-only strings next to structure may have shielded neighbours
    out=[t for t in out if not (isinstance(t,str) and not t.strip())]
    for i,t in enumerate(out):
        if not isinstance(t,str): continue
        k=i+1
        while k<len(out) and isinstance(out[k],dict) and ("f" in out[k] or "r" in out[k]): k+=1
        if k>=len(out) or STRUCT(out[k]): out[i]=t.rstrip()
        j=i-1
        while j>=0 and isinstance(out[j],dict) and ("f" in out[j] or "r" in out[j]): j-=1
        if j<0 or STRUCT(out[j]): out[i]=out[i].lstrip()
    out=[t for t in out if t!=""]
    # drop empty red spans and repeated breaks; drop trailing structure (belongs to no text)
    res=[]
    for t in out:
        if isinstance(t,dict) and t.get("r")==0 and res and isinstance(res[-1],dict) and res[-1].get("r")==1: res.pop();continue
        if isinstance(t,dict) and t.get("p") and res and isinstance(res[-1],dict) and res[-1].get("p"): continue
        res.append(t)
    while res and isinstance(res[-1],dict) and (res[-1].get("p") or ("l" in res[-1] and "h" not in res[-1])): res.pop()
    return res
