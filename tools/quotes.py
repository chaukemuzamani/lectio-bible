"""Quotation-mark analysis for texts that print curly quotes (“ ” ‘ ’)."""
import re
OPEN2,CLOSE2,OPEN1,CLOSE1="“","”","‘","’"
LET=re.compile(r"[^\W_]")
def _apos(text,i,st,open_at=None):
    prev=text[i-1] if i>0 else " ";nxt=text[i+1] if i+1<len(text) else " "
    if LET.match(prev) and LET.match(nxt): return True
    if OPEN1 not in st: return True
    if LET.match(nxt) and not LET.match(prev): return True     # ’tis
    # plural possessive (servants’ houses): letter s before, space + lowercase after,
    # and the open single quote is not a short quoted term just before
    if prev in "sS" and re.match(r" [a-z]",text[i+1:i+3]) and open_at is not None:
        span=text[open_at:i]
        if len(span.split())>4: return True
    return False
def scan(text,stack,breaks=()):
    """Events [(offset, kind, level)] with kind o=open c=close r=reopen x=stray, and the new stack.
    `breaks`: offsets where a paragraph or poetry line starts (offset 0 is always one)."""
    ev=[];st=list(stack);breaks=set(breaks)|{0}
    i=0;n=len(text)
    while i<n:
        ch=text[i]
        if i in breaks or (i>0 and text[:i].strip()=="" ):
            # run of quote marks at a paragraph start: reopen levels that are still open
            j=i;k=0
            while j<n and text[j] in (OPEN2,OPEN1,'"'):
                if text[j] in (OPEN2,OPEN1) and k<len(st) and st[k]==text[j]:
                    ev.append((j,"r",k));k+=1;j+=1;continue
                break
            if j>i: i=j;continue
        if ch==OPEN2:
            st.append(OPEN2);ev.append((i,"o",len(st)-1))
        elif ch==CLOSE2:
            if OPEN2 in st:
                while st and st[-1]!=OPEN2: st.pop()
                ev.append((i,"c",len(st)-1));st.pop()
            else: ev.append((i,"x",0))
        elif ch==OPEN1:
            prev=text[i-1] if i>0 else " ";nxt=text[i+1] if i+1<n else " "
            if LET.match(prev) and LET.match(nxt): ev.append((i,"a",0))      # misprinted apostrophe
            else: st.append(OPEN1);ev.append((i,"o",len(st)-1))
        elif ch==CLOSE1:
            oa=max([o for o,k,l in ev if k in "or" and text[o]==OPEN1],default=None)
            if not _apos(text,i,st,oa if oa is not None else -10**6):
                while st and st[-1]!=OPEN1: st.pop()
                if st: ev.append((i,"c",len(st)-1));st.pop()
        i+=1
    return ev,st
