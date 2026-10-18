import sys,pickle,collections;sys.path.insert(0,'.')
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
def check(code,show=5):
    K=pickle.load(open(Q+code+".pkl","rb"));bad=[]
    for b,chs in K.items():
        st=[]
        for ci,ch in enumerate(chs):
            for vi,v in enumerate(ch):
                for t in v:
                    if isinstance(t,dict) and "q" in t and not t.get("ro"):
                        if t["q"] in "“‘«„" and not (t["q"]=="“" and code.startswith("Rus")) and not (t["q"]=="“" and code=="CSlElizabeth"):
                            st.append((t.get("pid"),(ci+1,vi+1)))
                        else:
                            if not st or st[-1][0]!=t.get("pid"): bad.append((b,ci+1,vi+1,"close-mismatch",t.get("pid"),st[-1] if st else None))
                            if st: st.pop()
        if st: bad.append((b,"unclosed",st[:3]))
    print(code,"problems:",len(bad))
    for x in bad[:show]: print("   ",x)
for c in sys.argv[1:]: check(c)
