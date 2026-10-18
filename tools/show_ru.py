import sys,pickle;sys.path.insert(0,'.')
from audit_quotes import render
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
out=pickle.load(open(Q+sys.argv[1]+".pkl","rb"))
for spec in sys.argv[2:]:
    b,c,a,z=spec.split(":");c,a,z=int(c),int(a),int(z)
    for v in range(a,z+1):
        try: print(b,c,v,render(out[b][c-1][v-1]))
        except IndexError: pass
    print()
