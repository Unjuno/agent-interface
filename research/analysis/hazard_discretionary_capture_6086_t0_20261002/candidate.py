from fractions import Fraction as F
from itertools import combinations
import json
from pathlib import Path

cfg=json.loads(Path(__file__).with_name("freeze.json").read_text())
onsets=[F(i,2) for i in range(25)]
widths=[F(x) for x in cfg["cue_widths"]]
fixed={k:[F(x) for x in v] for k,v in cfg["schedules"].items() if isinstance(v,list)}
grid=[F(i,2) for i in range(24)]
def weight(kind,t):
    d=abs(t-F(5))
    if kind=="flat": return F(1)
    if kind=="peaked": return max(F(1),F(12)-2*d)
    return F(1)+2*d
def hit(starts,t,w):
    return any(s < t+w and s+F(1,2) > t for s in starts)
def score(starts,kind,w):
    ws=[weight(kind,t) for t in onsets]
    mass=sum((q for q,t in zip(ws,onsets) if hit(starts,t,w)),F(0))
    return mass/sum(ws)
def delay(starts,kind,w):
    pairs=[]
    for t in onsets:
        if hit(starts,t,w):
            s=min(s for s in starts if s<t+w and s+F(1,2)>t)
            pairs.append((weight(kind,t),max(F(0),s-t)))
    return sum((a*b for a,b in pairs),F(0))/sum((a for a,b in pairs),F(0))
rows=[]
for w in widths:
    oracle=max(combinations(grid,3),key=lambda ss:score(ss,"peaked",w))
    for d in ("peaked","flat","inverted"):
        row={"width":str(w),"distribution":d,"scores":{},"mean_delay":{}}
        for name,starts in fixed.items():
            row["scores"][name]=str(score(starts,d,w))
            row["mean_delay"][name]=str(delay(starts,d,w))
        row["scores"]["oracle"]=str(score(oracle,d,w))
        row["oracle_starts"]=[str(x) for x in oracle]
        rows.append(row)
print(json.dumps({"schema":"issue-6086-t0-candidate-v1","rows":rows,"onsets":[str(t) for t in onsets],"exposures_equal":True,"sentinels":[0,6,12],"miss_semantics":"NO_CUE only when no cue opportunity exists; capture miss is not absence/safety"},indent=2))
