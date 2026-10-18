"""Versification mapping between the reader's canonical KJV numbering and other systems.

Mapping files (*.vrs) are the Paratext/eBible versification files: each "X = Y" line maps a
verse in that system to the original-language (org/BHS) numbering. Unmentioned verses map to
themselves. The reader's canonical numbering is English (eng.vrs) with psalm titles (verse 0)
folded into verse 1, as the KJV prints them.
"""
import os,re,collections
HERE=os.path.dirname(os.path.abspath(__file__))
PROT=["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth","I Samuel","II Samuel","I Kings","II Kings","I Chronicles","II Chronicles","Ezra","Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon","Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts","Romans","I Corinthians","II Corinthians","Galatians","Ephesians","Philippians","Colossians","I Thessalonians","II Thessalonians","I Timothy","II Timothy","Titus","Philemon","Hebrews","James","I Peter","II Peter","I John","II John","III John","Jude","Revelation of John"]
USFM=["GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA","1KI","2KI","1CH","2CH","EZR","NEH","EST","JOB","PSA","PRO","ECC","SNG","ISA","JER","LAM","EZK","DAN","HOS","JOL","AMO","OBA","JON","MIC","NAM","HAB","ZEP","HAG","ZEC","MAL","MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL","EPH","PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS","1PE","2PE","1JN","2JN","3JN","JUD","REV"]
U2N=dict(zip(USFM,PROT))
REF=re.compile(r"^([0-9A-Z]{3}) (\d+):(\d+)(?:-(\d+))?$")
def _expand(s):
    m=REF.match(s.strip())
    if not m: return None
    b,c,v1,v2=m.group(1),int(m.group(2)),int(m.group(3)),m.group(4)
    return [(b,c,v) for v in range(v1,(int(v2) if v2 else v1)+1)]
class Vrs:
    def __init__(self,name):
        self.name=name;self.to_org=collections.defaultdict(list);self.from_org=collections.defaultdict(list);self.maxv={}
        for line in open(os.path.join(HERE,name+".vrs"),encoding="utf-8"):
            line=line.split("#",1)[0].strip()
            if not line: continue
            if "=" in line:
                a,b=line.split("=",1);A=_expand(a);B=_expand(b)
                if not A or not B: continue
                if len(A)==len(B): pairs=list(zip(A,B))
                elif len(A)==1: pairs=[(A[0],x) for x in B]
                elif len(B)==1: pairs=[(x,B[0]) for x in A]
                else: continue
                for x,y in pairs:
                    if y not in self.to_org[x]: self.to_org[x].append(y)
                    if x not in self.from_org[y]: self.from_org[y].append(x)
            else:
                parts=line.split()
                if re.match(r"^[0-9A-Z]{3}$",parts[0]) and all(re.match(r"^\d+:\d+$",p) for p in parts[1:]):
                    self.maxv[parts[0]]=[int(p.split(":")[1]) for p in parts[1:]]
    def org(self,r):
        return self.to_org.get(r) or [r]
    def native(self,o):
        return self.from_org.get(o) or ([o] if o not in self.to_org or o in self.to_org.get(o,[]) else [])
_cache={}
def V(name):
    if name not in _cache: _cache[name]=Vrs(name)
    return _cache[name]
def to_kjv(code,book,c,v):
    """Native (book,c,v) in system `code` -> list of canonical KJV refs (book,c,v)."""
    if code=="kjv": return [(book,c,v)]
    if book=="Psalms" and c>150: return []          # Psalm 151 has no place in the English numbering
    u=USFM[PROT.index(book)]
    out=[]
    for o in V(code).org((u,c,v)):
        for e in V("eng").native(o):
            b2,c2,v2=e
            if v2==0: v2=1
            r=(U2N.get(b2,book),c2,v2)
            if r not in out: out.append(r)
    return out
def from_kjv(code,book,c,v):
    """Canonical KJV (book,c,v) -> list of native refs in system `code`."""
    if code=="kjv": return [(book,c,v)]
    u=USFM[PROT.index(book)]
    srcs=[(u,c,v)]
    if v==1 and (u,c,0) in V("eng").to_org: srcs=[(u,c,0),(u,c,1)]
    out=[]
    for s in srcs:
        for o in V("eng").org(s):
            for n in V(code).native(o):
                r=(U2N.get(n[0],book),n[1],n[2])
                if r not in out: out.append(r)
    return out
if __name__=="__main__":
    for code in ["rso","org","vul"]:
        for r in [("Genesis",31,55),("Numbers",12,16),("Numbers",13,1),("Psalms",3,1),("Psalms",23,1),("Psalms",51,1),("Malachi",4,1),("Joel",2,28),("Romans",16,25),("Romans",14,23)]:
            print(code,r,"->",from_kjv(code,*r),"  back",[to_kjv(code,*x) for x in from_kjv(code,*r)])
