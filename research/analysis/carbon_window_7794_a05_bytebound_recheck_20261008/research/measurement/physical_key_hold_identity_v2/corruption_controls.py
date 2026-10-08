import copy,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;r=json.loads((HERE/'RESULT.json').read_text())
def valid(x):return x.get('decision')=='PASS_PHYSICAL_HOLD_IDENTITY_CONSTRUCTION_V2_SCOPED' and x.get('seed')==99920260917002 and x.get('chunks')==x.get('chunks_complete')==25 and x.get('lifetimes')==250000 and all(v==0 for v in x.get('counts',{}).values()) and x.get('reruns')==0
controls=[]
for name,fn in [('seed',lambda x:x.update(seed=1)),('missing_chunk',lambda x:x.update(chunks_complete=24)),('reuse',lambda x:x['counts'].update(retired_reuse=1)),('mismatch',lambda x:x['counts'].update(mismatches=1)),('rerun',lambda x:x.update(reruns=1))]:
 y=copy.deepcopy(r);fn(y);controls.append({'name':name,'rejected':not valid(y)})
out={'passed':all(x['rejected'] for x in controls),'controls':controls};(HERE/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
