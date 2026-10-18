import pickle,sys;sys.path.insert(0,'.')
from audit_quotes import render
Q="/tmp/claude-0/-home-claude/8845616c-d446-5a26-8eb6-b26a8def4de5/scratchpad/q/"
code=sys.argv[1];d=pickle.load(open(Q+code+".pkl","rb"))
for spec in sys.argv[2:]:
    b,c,a,z=spec.split(":");c,a,z=int(c),int(a),int(z)
    for v in range(a,z+1):
        try: print(f"{b} {c}:{v}",render(d[b][c-1][v-1]))
        except IndexError: pass
    print()
