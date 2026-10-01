import copy,json
from audit import audit
from pathlib import Path
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'formal-output/FORMAL_RESULT.json').read_text())
controls=[]
def mutate(name,fn):
 x=copy.deepcopy(r); fn(x); controls.append({'name':name,'rejected':not audit(x)['passed']})
mutate('candidate_multiwinner',lambda x:x['primary'][1].__setitem__('owner_count',2))
mutate('candidate_zero_winner',lambda x:x['primary'][1].__setitem__('owner_count',0))
mutate('wrong_task_ref',lambda x:x['primary'][1].__setitem__('task_ref','refs/experiment-claims/'+'0'*64))
mutate('winner_object_mutation',lambda x:x['primary'][1]['final_object'].__setitem__('worker_id','forged'))
mutate('primary_count_corruption',lambda x:x['primary'].pop())
out={'schema':'experiment_task_cas_claim_corruption_v1','controls':controls,'all_rejected':all(c['rejected'] for c in controls)}
(HERE/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
