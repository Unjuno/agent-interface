"""Independent exhaustive oracle; uses integer half-units, no candidate imports."""
from fractions import Fraction as Q
from itertools import combinations
import json
from pathlib import Path
cfg=json.loads(Path(__file__).with_name("freeze.json").read_text())
starts={"uniform":(2,10,18),"phase_diversified":(4,12,20),"hazard":(8,10,12)}
ticks=range(25)
grid=range(24)
def wt(k,i):
    dist=abs(Q(i,2)-5)
    if k=="flat": return 1
    if k=="peaked": return max(Q(1),Q(12)-2*dist)
    return 1+2*dist
def seen(ss,i,width_ticks):
    return any(j < i+width_ticks and j+1 > i for j in ss)
def calc(ss,k,width_ticks):
    den=sum(wt(k,i) for i in ticks)
    num=sum(wt(k,i) for i in ticks if seen(ss,i,width_ticks))
    return Q(num,den)
rows=[]
for width_ticks in (1,2):
    best=max(combinations(grid,3),key=lambda z:calc(z,"peaked",width_ticks))
    for dist in ("peaked","flat","inverted"):
        rows.append({"width":str(Q(width_ticks,2)),"distribution":dist,"scores":{n:str(calc(ss,dist,width_ticks)) for n,ss in starts.items()}|{"oracle":str(calc(best,dist,width_ticks))},"oracle_starts":[str(Q(i,2)) for i in best]})
print(json.dumps({"schema":"issue-6086-t0-independent-oracle-v1","rows":rows},indent=2))
