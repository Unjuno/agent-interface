from copy import deepcopy
import json,tempfile,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
facts=json.loads((HERE/'facts.json').read_text()); result=json.loads((HERE/'RESULT.json').read_text())
def reject(name,f):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'f.json';r=Path(d)/'r.json';p.write_text(json.dumps(f));r.write_text(json.dumps(result))
        out=json.loads(subprocess.check_output([sys.executable,str(HERE/'audit.py'),str(p),str(r)]))
    return {'name':name,'rejected':not out['audit_pass'],'errors':out['errors']}
rows=[]
f=deepcopy(facts);f['live_gates'][0]['status']='PROVEN_LIVE';rows.append(reject('promote_1099_plan_to_live',f))
f=deepcopy(facts);next(x for x in f['implementation_nodes'] if x['id']=='v12_offline')['class']='LIVE_PHYSICAL_RECEIPT';rows.append(reject('offline_to_live_class',f))
f=deepcopy(facts);next(x for x in f['implementation_nodes'] if x['id']=='stable_hold_identity')['decision']='PASS_FAKE';rows.append(reject('identity_decision',f))
f=deepcopy(facts);next(x for x in f['implementation_nodes'] if x['id']=='clock_provenance_gate')['decision']='PASS_FAKE';rows.append(reject('clock_gate_decision',f))
f=deepcopy(facts);f['live_gates'][2]['status']='PROVEN_LIVE';rows.append(reject('claim_as_clock_proof',f))
f=deepcopy(facts);next(x for x in f['semantic_nodes'] if x['id']=='effect_provenance')['class']='LIVE_EFFECT';rows.append(reject('synthetic_effect_to_live',f))
print(json.dumps({'all_rejected':all(x['rejected'] for x in rows),'rows':rows},sort_keys=True,indent=2))
