"""Helpers: flat text of a token verse, with break offsets."""
def flat(toks):
    text="";breaks=set();spans=[]
    if isinstance(toks,str): return toks,{0},[(0,len(toks),0)]
    for i,t in enumerate(toks):
        if isinstance(t,str): spans.append((len(text),len(text)+len(t),i));text+=t
        elif isinstance(t,list):
            s=t[0]
            if len(t)>=6 and text and not text.endswith(" "): text+=" "
            spans.append((len(text),len(text)+len(s),i));text+=s
        elif isinstance(t,dict) and (t.get("p") or t.get("br") or t.get("d")==0 or ("l" in t and "h" not in t)):
            breaks.add(len(text))
            if text and not text.endswith(" "): text+=" "
            breaks.add(len(text))
    return text,breaks,spans
