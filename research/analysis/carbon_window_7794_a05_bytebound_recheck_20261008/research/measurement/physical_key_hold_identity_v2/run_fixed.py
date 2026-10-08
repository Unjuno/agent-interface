from __future__ import annotations
import json
from pathlib import Path
from model import Candidate,Event,LifecycleError
from oracle import HistoryOracle
p=Path('results/FIXED.json')
if p.exists(): raise RuntimeError('fixed output exists; rerun forbidden')
p.parent.mkdir(exist_ok=True)
def replay(events):
 c=Candidate();o=HistoryOracle();outs=[]
 for e in events:
  co=c.step(e);oo=o.step(e);assert co==oo and c.snapshot()==o.snapshot();outs.append(co)
 return outs,c.snapshot()
controls=[]
def ok(name,events,check):
 try: outs,state=replay(events);passed=check(outs,state);detail={'outs':outs,'state':state}
 except Exception as ex: passed=False;detail=type(ex).__name__
 controls.append({'name':name,'pass':passed,'detail':detail})
E=Event
ok('single_hold',[E('down','o','i','K',True),E('up','o','i','K',True)],lambda x,s:x[0][0]=='MINTED' and x[1][0]=='RETIRED' and x[0][1]==x[1][1])
ok('repeated_down',[E('down','o','i','K',True),E('down','o','i','K',False),E('down','o','i','K',True)],lambda x,s:x[1][0]==x[2][0]=='ACTIVE_REUSED' and x[0][1]==x[1][1]==x[2][1])
ok('sequential_holds',[E('down','o','i','K',True),E('up','o','i','K',True),E('down','o','i','K',True)],lambda x,s:x[0][1]=='o:g1:K' and x[2][1]=='o:g2:K')
ok('preexisting_unconfirmed',[E('down','o','i','K',False)],lambda x,s:x==[('UNCONFIRMED_DOWN_NO_ID',None)] and not s['active'])
ok('up_without_generation',[E('up','o','i','K',True)],lambda x,s:x==[('NO_ACTIVE',None)])
ok('wrong_intent_retire',[E('down','o','i','K',True),E('up','o','j','K',True)],lambda x,s:x[1]==('LINEAGE_MISMATCH',None) and len(s['active'])==1)
ok('wrong_owner_rebind',[E('down','o','i','K',True),E('down','p','i','K',True)],lambda x,s:x[1]==('LINEAGE_MISMATCH',None) and len(s['active'])==1)
ok('cleanup',[E('down','o','i','K',True),E('cleanup','o','i','K',True)],lambda x,s:x[1][0]=='RETIRED' and not s['active'])
ok('duplicate_terminal',[E('down','o','i','K',True),E('up','o','i','K',True),E('up','o','i','K',True)],lambda x,s:x[2]==('NO_ACTIVE',None))
ok('counter_monotonic',[E('down','o','i','A',True),E('up','o','i','A',True),E('down','o','i','B',True)],lambda x,s:x[0][1]=='o:g1:A' and x[2][1]=='o:g2:B')
malformed=[]
for ev in [E('bogus','o','i','K',True),E('down','','i','K',True),E('down','o','i','K',1)]:
 try: Candidate().step(ev); malformed.append(False)
 except LifecycleError: malformed.append(True)
controls.append({'name':'malformed_events','pass':all(malformed),'detail':malformed})
out={'schema':'physical_key_hold_identity_fixed_v2','controls':controls,'passed':all(x['pass'] for x in controls),'controls_passed':sum(x['pass'] for x in controls),'controls_total':len(controls),'reruns':0}
p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
