"""Parse OSIS with verse milestones (Open English Bible) into token lists."""
import re
from vrs import PROT
OSIS2N={"Gen":"Genesis","Exod":"Exodus","Lev":"Leviticus","Num":"Numbers","Deut":"Deuteronomy","Josh":"Joshua","Judg":"Judges","Ruth":"Ruth","1Sam":"I Samuel","2Sam":"II Samuel","1Kgs":"I Kings","2Kgs":"II Kings","1Chr":"I Chronicles","2Chr":"II Chronicles","Ezra":"Ezra","Neh":"Nehemiah","Esth":"Esther","Job":"Job","Ps":"Psalms","Prov":"Proverbs","Eccl":"Ecclesiastes","Song":"Song of Solomon","Isa":"Isaiah","Jer":"Jeremiah","Lam":"Lamentations","Ezek":"Ezekiel","Dan":"Daniel","Hos":"Hosea","Joel":"Joel","Amos":"Amos","Obad":"Obadiah","Jonah":"Jonah","Mic":"Micah","Nah":"Nahum","Hab":"Habakkuk","Zeph":"Zephaniah","Hag":"Haggai","Zech":"Zechariah","Mal":"Malachi","Matt":"Matthew","Mark":"Mark","Luke":"Luke","John":"John","Acts":"Acts","Rom":"Romans","1Cor":"I Corinthians","2Cor":"II Corinthians","Gal":"Galatians","Eph":"Ephesians","Phil":"Philippians","Col":"Colossians","1Thess":"I Thessalonians","2Thess":"II Thessalonians","1Tim":"I Timothy","2Tim":"II Timothy","Titus":"Titus","Phlm":"Philemon","Heb":"Hebrews","Jas":"James","1Pet":"I Peter","2Pet":"II Peter","1John":"I John","2John":"II John","3John":"III John","Jude":"Jude","Rev":"Revelation of John"}
TOK=re.compile(r"<!--.*?-->|<(/?)([\w:]+)((?:\s+[\w:-]+=\"[^\"]*\")*)\s*(/?)>|([^<]+)",re.S)
def attr(a,k):
    m=re.search(r'\b'+k+r'="([^"]*)"',a or "");return m.group(1) if m else None
def parse(path):
    s=open(path,encoding="utf-8").read()
    books={};cur=None;c=0;v=0;inv=False;pend=[];stack=[];note=None;title=None;red_open=False
    def tgt(): return books[cur][c-1][v-1] if inv else pend
    def put(x):
        if cur is None or c==0: return
        tgt().append(x)
    for m in TOK.finditer(s):
        if m.group(0).startswith("<!--"): continue
        close,tag,attrs,selfc,tx=m.groups()
        if tx is not None:
            if note is not None:
                if "reference" in stack[-1:]: continue
                note.append(tx);continue
            if title is not None: title["buf"].append(tx);continue
            if "header" in stack: continue
            if cur and c and (inv or tx.strip()): put(tx)
            continue
        if tag=="div" and not close and attr(attrs,"type")=="book":
            cur=OSIS2N.get(attr(attrs,"osisID"));c=v=0;inv=False;pend=[]
            if cur: books[cur]=[]
            if not selfc: stack.append(tag)
            continue
        if tag=="chapter" and selfc and attr(attrs,"sID") and cur:
            c=int(attr(attrs,"n") or attr(attrs,"sID").split(".")[-1]);v=0;inv=False
            while len(books[cur])<c: books[cur].append([])
            continue
        if tag=="verse" and selfc and cur and c:
            if attr(attrs,"sID"):
                v=int(attr(attrs,"n") or attr(attrs,"sID").split(".")[-1]);inv=True
                ch=books[cur][c-1]
                while len(ch)<v: ch.append([])
                if pend: ch[v-1].extend(pend);pend=[]
                if red_open: ch[v-1].append({"r":1})
            elif attr(attrs,"eID"):
                if red_open and inv: put({"r":0})
                inv=False
            continue
        if selfc:
            if tag=="lb" and attr(attrs,"type")=="x-p": put({"p":1})
            continue
        if not close:
            stack.append(tag)
            if tag=="note": note=[]
            elif tag=="title":
                typ=attr(attrs,"type")
                title={"type":typ,"buf":[]} if typ!="main" else {"type":"main","buf":[]}
            elif tag=="q" and attr(attrs,"who")=="Jesus": red_open=True;put({"r":1})
            elif tag=="p": put({"p":1})
            elif tag=="lg": put({"p":1})
            elif tag=="l": put({"l":int(attr(attrs,"level") or 1)})
            continue
        if tag=="note" and note is not None:
            t=re.sub(r"\s+"," ","".join(note)).strip();note=None
            if t: put({"f":t})
        elif tag=="title" and title is not None:
            t=re.sub(r"\s+"," ","".join(title["buf"])).strip();typ=title["type"];title=None
            if t and cur and c:
                if typ=="psalm": put({"d":1});put(t);put({"d":0})
                elif typ!="main": put({"h":re.sub(r"^Psalm \d+\s*[–-]\s*","",t),"l":1})
        elif tag=="q" and red_open: red_open=False;put({"r":0})
        if stack and stack[-1]==tag: stack.pop()
        elif tag in stack:
            while stack and stack[-1]!=tag: stack.pop()
            if stack: stack.pop()
    import usfx
    return {b:[[usfx.tidy(vs) for vs in ch] for ch in chs] for b,chs in books.items()}
