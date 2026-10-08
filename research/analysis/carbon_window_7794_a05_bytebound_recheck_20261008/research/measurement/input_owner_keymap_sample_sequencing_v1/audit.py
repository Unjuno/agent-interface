import hashlib,json,random
from pathlib import Path
import baseline,candidate
from common import make_case,state_tuple,strip_samples
from runner import check_order
ROOT=Path(__file__).resolve().parent
F=json.loads((ROOT/'FREEZE.json').read_text()); R=json.loads((ROOT/'RESULT.json').read_text())
errors=[]
if R['random_cases']!=F['random_cases']: errors.append('random_count')
if R['random_mismatches']!=0: errors.append('runner_mismatch')
if R['order_errors']!=0: errors.append('runner_order')
if R['sample_fail_semantic_changes']!=0: errors.append('sample_failure_changed_semantics')
if any(R['forbidden_claims'].values()): errors.append('forbidden_claim')
# independent second seeded corpus; independently spell comparison rather than using runner.compare
rng=random.Random(F['audit_seed']); mismatches=order_errors=0; h=hashlib.sha256()
for i in range(F['audit_cases']):
    c=make_case(rng)
    bs,bo=baseline.execute(c); cs,co=candidate.execute(c)
    equal = (bo.ok==co.ok and bo.result==co.result and bo.error==co.error and strip_samples(cs.trace)==bs.trace and state_tuple(cs)==state_tuple(bs))
    order=check_order(c,cs.trace)
    if not equal:mismatches+=1
    if not order:order_errors+=1
    h.update(f"{i}:{int(equal)}:{int(order)}\n".encode())
if mismatches:errors.append(f'audit_mismatches:{mismatches}')
if order_errors:errors.append(f'audit_order:{order_errors}')
# source/package hashes for immutable construction record
files=['FREEZE.json','baseline.py','candidate.py','common.py','runner.py','audit.py','EXPERIMENT_CHARTER.md','ROADMAP.md']
sha={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
out={'decision':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','audit_cases':F['audit_cases'],'mismatches':mismatches,'order_errors':order_errors,'audit_digest':h.hexdigest(),'source_sha256':sha,'errors':errors}
(ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True))
print(json.dumps(out,sort_keys=True))
