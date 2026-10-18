import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
"""Where people speak: quotation structure from the WEB and BSB, keyed by KJV-numbered verse.

For each book the two sources are scanned in parallel. The text is cut into regions at verse
boundaries where neither source has a quotation open; each region takes the WEB's quotation
marks if they are well-formed there (closest wording to the older English versions), otherwise
the BSB's.
"""
import quotes,wstruct,sources
from vrs import PROT
def web_verse(W,b,c,v):
    if b=="Romans" and c==16 and v in (25,26,27): c,v=14,v-1
    if b=="Romans" and c==14 and v>23: return []
    try: return W[b][c-1][v-1]
    except Exception: return []
def build():
    W=sources.webu();B=sources.bsbu();out={};stats={"WEB":0,"BSB":0,"messy":0}
    for b in PROT:
        keys=[(b,ci+1,vi+1) for ci,ch in enumerate(B[b]) for vi,_ in enumerate(ch)]
        rows=[]
        for src,get in (("WEB",lambda k:web_verse(W,*k)),("BSB",lambda k:B[k[0]][k[1]-1][k[2]-1])):
            st=[];seq=[]
            for k in keys:
                toks=get(k)
                text,br,_=wstruct.flat(toks)
                # end of a psalm superscription: quotation marks inside titles are not carried over
                tend=0
                if any(isinstance(t,dict) and t.get("d")==0 for t in toks):
                    tend=len(wstruct.flat(toks[:[i for i,t in enumerate(toks) if isinstance(t,dict) and t.get("d")==0][0]])[0])
                start=list(st)
                ev,st=quotes.scan(text,st,br)
                ev=[e for e in ev if e[0]>=tend]
                seq.append({"text":text,"start":start,"ev":ev})
            rows.append(seq)
        Wq,Bq=rows
        # region boundaries
        cuts=[i for i in range(len(keys)) if not Wq[i]["start"] and not Bq[i]["start"]]+[len(keys)]
        for a,z in zip(cuts,cuts[1:]):
            def clean(seq):
                if any(e[1]=="x" for i in range(a,z) for e in seq[i]["ev"]): return False
                if z<len(keys) and seq[z]["start"]: return False
                if any(len(seq[i]["start"])>3 for i in range(a,z)): return False
                return True
            pick=Wq if clean(Wq) else Bq if clean(Bq) else Wq
            name="WEB" if pick is Wq else "BSB"
            if not clean(pick): stats["messy"]+=1
            stats[name]+=1
            stack=[]
            for i in range(a,z):
                r=pick[i];evs=[]
                for e in r["ev"]:
                    if e[1]=="o":
                        pid=f"{b}|{keys[i][1]}|{keys[i][2]}|{e[0]}";stack.append((e[2],pid));evs.append((e[0],"o",e[2],pid))
                    elif e[1]=="c":
                        while stack and stack[-1][0]>e[2]: stack.pop()
                        if stack and stack[-1][0]==e[2]:
                            pid=stack.pop()[1];evs.append((e[0],"c",e[2],pid))
                if i==len(keys)-1 and stack:
                    # a quotation still open when the book ends closes with the book
                    while stack:
                        lvl,pid=stack.pop();evs.append((len(r["text"].rstrip()),"c",lvl,pid))
                if evs or r["start"]:
                    out[keys[i]]={"src":name,"text":r["text"],"depth":len(r["start"]),"ev":evs}
    return out,stats
if __name__=="__main__":
    o,s=build();print(len(o),"verses with speech",s)
