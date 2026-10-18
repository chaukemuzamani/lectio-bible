"""Turn straight quotation marks into typographic ones, pairing them properly.

YLT opens with ` and closes with '; JPS uses '...'; NHEB uses "..." with '...' inside.
Apostrophes become ’. Nesting levels alternate “ ” / ‘ ’.
"""
import re
OPEN={0:"“",1:"‘"};CLOSE={0:"”",1:"’"}
def _lvl(n): return n%2
def is_let(c): return c.isalpha()
def ylt(text,st,first=False):
    out=[];n=len(text)
    for i,ch in enumerate(text):
        a=text[i-1] if i else " ";z=text[i+1] if i+1<n else " "
        if ch=="`":
            if first and not text[:i].strip() and st:      # reopening mark at the start of a verse
                out.append(OPEN[_lvl(len(st)-1)]);continue
            out.append(OPEN[_lvl(len(st))]);st.append(1)
        elif ch=="'":
            if is_let(a) and is_let(z): out.append("’")
            elif st and not (is_let(a) and z==" "):
                st.pop();out.append(CLOSE[_lvl(len(st))])
            else: out.append("’")
        else: out.append(ch)
    s="".join(out).replace("--","—")
    s=re.sub(r"([“‘]) +",r"\1",s)
    return s,st
def jps(text,st,first=False):
    out=[];n=len(text)
    for i,ch in enumerate(text):
        a=text[i-1] if i else " ";z=text[i+1] if i+1<n else " "
        if ch=="'":
            if is_let(a) and is_let(z): out.append("’")
            elif (not is_let(a)) and (is_let(z) or z in "‘“("):
                out.append(OPEN[_lvl(len(st))]);st.append(1)
            elif st and not (is_let(a) and z==" "):
                st.pop();out.append(CLOSE[_lvl(len(st))])
            else: out.append("’")
        elif ch=='"':
            if not is_let(a) and a not in ".,;:?!" : out.append(OPEN[_lvl(len(st))]);st.append(1)
            elif st: st.pop();out.append(CLOSE[_lvl(len(st))])
            else: out.append("”")
        else: out.append(ch)
    return "".join(out).replace("--","—"),st
def nheb(text,st,first=False):
    out=[];n=len(text)
    for i,ch in enumerate(text):
        a=text[i-1] if i else " ";z=text[i+1] if i+1<n else " "
        if ch=='"':
            if (i==0 or a in " ([—-'‘“") and z!=" ": out.append("“")
            else: out.append("”")
        elif ch=="'":
            if (i==0 or a in ' (["“—-') and (is_let(z) or z in "“\"("): out.append("‘")
            else: out.append("’")
        else: out.append(ch)
    s="".join(out)
    s=re.sub(r"“ +","“",s)
    return s,st
FN={"YLT":ylt,"JPS":jps,"NHEBME":nheb}
def normalize_books(code,books,depth_of=None):
    """depth_of(book,c,v) -> how many quotations the WEB/BSB have open at the start of that verse;
    used to resynchronise when a version leaves a quotation unclosed."""
    fn=FN[code]
    for b,chs in books.items():
        st=[]
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                if depth_of:
                    d=depth_of(b,ci+1,vi+1)
                    if d is not None and len(st)>d: st=st[:d]
                first=True
                for i,t in enumerate(v):
                    if isinstance(t,str): v[i],st=fn(t,st,first);first=False
    return books
