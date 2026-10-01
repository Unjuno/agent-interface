from __future__ import annotations
import hashlib,json,random
from pathlib import Path
from normalizer import normalize_one,normalize_stream
from oracle import oracle
from queue_contract import reduce_candidate
from run_formal import SEED,VALID,INVALID,valid_case,invalid_case
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'RESULT.json').read_text()); rng=random.Random(SEED); h=hashlib.sha256(); vm=ia=ce=re=0; kinds={}; batch=[]
for i in range(VALID):
    e=valid_case(rng,i); n=normalize_one(e); o=oracle(e); vm+=n['normalization']['kind']!=o['kind']; re+=n['raw']!=o['raw'] or n['raw']!=e['raw']; kinds[n['normalization']['kind']]=kinds.get(n['normalization']['kind'],0)+1; h.update(json.dumps([e['event_id'],n['normalization']['kind']],separators=(',',':')).encode()); batch.append(e)
    if len(batch)==10:
        ns=normalize_stream(batch); q=reduce_candidate([x['record'] for x in ns],2_000_000_000,0); ids=[x['event_id'] for x in batch]; ce+=q['delivered_ids']!=ids or q['critical_ids']!=ids or q['grants_input_authority']; batch=[]
for i in range(INVALID):
    e=invalid_case(rng,VALID+i); ca=oa=False
    try: normalize_one(e); ca=True
    except ValueError: pass
    try: oracle(e); oa=True
    except ValueError: pass
    ia+=ca or oa; h.update(json.dumps(['invalid',i,ca,oa],separators=(',',':')).encode())
checks={'decision':r['decision']=='PASS_INPUT_OWNER_CRITICAL_NORMALIZATION_SCOPED','counts':(r['valid_records'],r['invalid_records'])==(VALID,INVALID),'errors_zero':(vm,ia,ce,re)==(0,0,0,0)==(r['valid_mismatches'],r['invalid_accepted'],r['composition_errors'],r['raw_provenance_errors']),'kinds':r['kind_counts']==kinds,'digest':r['digest']==h.hexdigest(),'formal':(r['formal_invocation'],r['reruns'])==(1,0),'sources':r['source_git_blobs']=={'input_owner_v10':'341b3c01649943ddaad5f28431a792c4889cc36e','queue_contract':'404a452aa304b4bde73ec0182450d241e2a744af','#1032_RESULT':'f9afddd78ad2221e45dc9f69d304362ed1a3abbb'},'no_actions':all(r[k]==0 for k in ['model_calls','gui_actions','task_input_actions','authority_actions'])}
out={'schema':'input_owner_critical_normalization_audit_v1','passed':all(checks.values()),'checks':checks,'errors':[k for k,v in checks.items() if not v]}; (HERE/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print('AUDIT_PASS' if out['passed'] else out)
