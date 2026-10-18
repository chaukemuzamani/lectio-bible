import sys,pickle,re,collections;sys.path.insert(0,'.')
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
K=pickle.load(open(Q+"KJVS.pkl","rb"))
from vrs import PROT
# walk words with red state and quote depth
W=[]  # (ref, word, red, depth)
for b in PROT[39:]:
    depth=0
    for ci,ch in enumerate(K[b]):
        for vi,v in enumerate(ch):
            red=False
            for t in v:
                if isinstance(t,dict):
                    if "r" in t: red=bool(t["r"])
                    if "q" in t and not t.get("ro"):
                        if t["q"] in "“‘": depth+=1
                        else: depth=max(0,depth-1)
                elif isinstance(t,(str,list)):
                    s=t if isinstance(t,str) else t[0]
                    for w in re.findall(r"[A-Za-z]+",s): W.append(((b,ci+1,vi+1),w,red,depth))
# (a) red words outside quotes
miss=collections.Counter(r for r,w,red,d in W if red and d==0)
print("red outside quotes:",sum(miss.values()),"in",len(miss),"verses")
for r,n in miss.most_common(40): print("  ",r,n)
# (b) non-red runs inside quotes with red neighbours
runs=collections.Counter();i=0
while i<len(W):
    if W[i][3]>0 and not W[i][2]:
        j=i
        while j<len(W) and W[j][3]>0 and not W[j][2]: j+=1
        if i>0 and W[i-1][2] and j<len(W) and W[j][2] and j-i>=3: runs[W[i][0]]=j-i
        i=j
    else: i+=1
print("non-red runs inside red quotes:",len(runs))
for r,n in runs.most_common(40): print("  ",r,n)
