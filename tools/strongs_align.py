"""Statistical word alignment to Strong's numbers (Python port of the reader's alignWords).

Used for Russian, Church Slavonic and Shona, which have no word tags."""
import re,json,os
from lib import DATA,load
WORDRE={"en":re.compile(r"[A-Za-z’']+"),"ru":re.compile(r"[А-Яа-яЁёІіѢѣѲѳѴѵ]+"),"sn":re.compile(r"[A-Za-z']+")}
STOP={"ru":set("и в во не на что с со как к ко по из у о об а же от но я он она они оно мы вы ты его ее её их им ему ей нам вам тебе тебя меня мне себя свой своей свою своих это то так ли бы да для до за при же сей сия сие".split()),"sn":set(),"en":set()}
def stem(w,lang):
    if lang=="ru": w=w.lower().replace("ё","е");return w[:5] if len(w)>5 else w
    if lang=="sn": w=w.lower();return w[:7] if len(w)>7 else w
    return w.lower()
_tables={}
def table(code):
    if code not in _tables: _tables[code]=json.load(open(f"{DATA}/align/{code}.json"))
    return _tables[code]
_ref={}
def refbooks():
    if not _ref:
        _ref["HEB"]=load("HEB");_ref["GRK"]=load("GRK");_ref["TR"]=load("TR")
    return _ref
def ref_strongs(book,c,v):
    from vrs import PROT
    R=refbooks();nt=PROT.index(book)>=39;S=set()
    for src in (["GRK","TR"] if nt else ["HEB"]):
        try: vv=R[src][book][c-1][v-1]
        except Exception: continue
        if isinstance(vv,list):
            for t in vv:
                if isinstance(t,list) and len(t)>=6:
                    for x in t[1].split():
                        if x and not re.match(r"H9\d{3}$",x): S.add(x)
    return S
def align_words(code,words,S):
    """words: list of word strings. Returns {index: strong} using the confident passes only."""
    tb=table(code);lang=tb["lang"];rev=tb["r"];stop=STOP.get(lang,set())
    stems=[stem(w,lang) for w in words];out={};used={}
    cand=[]
    for i,w in enumerate(stems):
        if w in stop or len(w)<2: continue
        for s,sc in rev.get(w,()):
            if sc>=8 and s in S: cand.append((sc,i,s))
    cand.sort(reverse=True)
    for sc,i,s in cand:
        if i in out or used.get(s,0)>=2: continue
        out[i]=s;used[s]=used.get(s,0)+1
    cand=[]
    for i,w in enumerate(stems):
        if i in out or w in stop or len(w)<2: continue
        for s,sc in rev.get(w,()):
            if sc>=2 and s in S and not used.get(s): cand.append((sc,i,s))
    cand.sort(reverse=True)
    for sc,i,s in cand:
        if i in out or used.get(s): continue
        out[i]=s;used[s]=1
    return out

def candidates(code,words,S,minsc=2):
    """For every word, the Strong's numbers of this verse it may translate (statistical table)."""
    tb=table(code);lang=tb["lang"];rev=tb["r"];stop=STOP.get(lang,set())
    out=[]
    for w in words:
        st=stem(w,lang)
        if st in stop or len(st)<2: out.append(set());continue
        out.append({s for s,sc in rev.get(st,()) if sc>=minsc and s in S})
    return out
