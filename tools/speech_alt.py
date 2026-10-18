"""Alternative speech sources for passages where the WEB cannot serve every version:
Textus Receptus wording (Acts 9:5-6, Luke 17:36) and a few WEB quotation slips.
Each region is used for a version when its wording fits that version at least as well."""
import quotes
REGIONS=[
 {"force":False,"v":{
   ("Acts",9,5):"He said, “Who are you, Lord?” The Lord said, “I am Jesus, whom you are persecuting. It is hard for you to kick against the goads.”",
   ("Acts",9,6):"He, trembling and astonished, said, “Lord, what will you have me to do?” The Lord said to him, “Arise, and go into the city, and you will be told what you must do.”"}},
 {"force":False,"v":{
   ("Luke",17,36):"“Two will be in the field: the one will be taken, and the other will be left.”"}},
 {"force":True,"v":{
   ("Mark",12,35):"Jesus responded, as he taught in the temple, “How is it that the scribes say that the Christ is the son of David?",
   ("Mark",12,36):"For David himself said in the Holy Spirit, ‘The Lord said to my Lord, “Sit at my right hand, until I make your enemies the footstool of your feet.”’",
   ("Mark",12,37):"Therefore David himself calls him Lord, so how can he be his son?” The common people heard him gladly."}},
]
def events(region):
    st=[];out={};stack=[]
    for ref,text in region["v"].items():
        depth=len(st);ev,st=quotes.scan(text,st,{0});evs=[]
        for e in ev:
            if e[1]=="o":
                pid=f"alt|{ref[0]}|{ref[1]}|{ref[2]}|{e[0]}";stack.append((e[2],pid));evs.append((e[0],"o",e[2],pid))
            elif e[1]=="c":
                while stack and stack[-1][0]>e[2]: stack.pop()
                if stack and stack[-1][0]==e[2]: evs.append((e[0],"c",e[2],stack.pop()[1]))
        out[ref]={"src":"ALT","text":text,"depth":depth,"ev":evs}
    return out

_ev=None
def apply(sp,text_of):
    """sp with the alternative regions swapped in where they fit the version better.
    text_of(kjv_ref) -> the version's plain text for that verse (or None)."""
    import align_en
    global _ev
    if _ev is None: _ev=[events(r) for r in REGIONS]
    out=dict(sp)
    for r,ev in zip(REGIONS,_ev):
        if r["force"]:
            out.update(ev);continue
        sa=sm=0;n=0
        for ref,e in ev.items():
            t=text_of(ref)
            if not t: continue
            tw=align_en.words(t);n+=1
            sa+=align_en.anchors(align_en.words(e["text"]),tw)[1]
            if ref in sp: sm+=align_en.anchors(align_en.words(sp[ref]["text"]),tw)[1]
        if n and sa>=sm+0.05*n:
            for ref in ev: out.pop(ref,None)
            out.update(ev)
    return out
