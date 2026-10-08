from __future__ import annotations
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
L=json.loads((ROOT/'LEDGER.json').read_text()); R=json.loads((ROOT/'RESULT.json').read_text())
REQ=['model_facing','same_task_fixture','same_underlying_semantic_evidence','same_definitions','same_model_effort','same_prompt_schema_except_representation','same_execution_policy','same_session_cache_treatment','independent_outcome_accounting','representation_only_difference','canonical_vs_compact_same_meaning']
errs=[]
expected={}
for f in L['families']:
    failed=[k for k in REQ if f['gates'].get(k) is not True]
    expected[f['id']]={'admissible':not failed,'failed_gates':failed,'git_blob':f['git_blob'],'path':f['path']}
rows={r['id']:r for r in R.get('rows',[])}
if set(rows)!=set(expected): errs.append('row_set')
for k,e in expected.items():
    r=rows.get(k,{})
    for fld in ['admissible','failed_gates','git_blob','path']:
        if r.get(fld)!=e[fld]: errs.append(f'{k}:{fld}')
adm=sum(int(e['admissible']) for e in expected.values())
if R.get('admissible_pairs')!=adm: errs.append('admissible_count')
exp_dec='PASS_RETAINED_SYMBOL_REPRESENTATION_IDENTIFIABLE_SCOPED' if adm else ('HOLD_NO_RETAINED_SYMBOL_REPRESENTATION_CONTRAST' if len(expected)>=4 and all(e['failed_gates'] for e in expected.values()) else 'FAIL_INTEGRITY')
if R.get('decision')!=exp_dec: errs.append('decision')
if R.get('formal_invocations')!=1 or R.get('reruns')!=0: errs.append('invocation')
if R.get('ledger_sha256')!=hashlib.sha256((ROOT/'LEDGER.json').read_bytes()).hexdigest(): errs.append('ledger_hash')
out={'pass':not errs,'errors':errs,'decision':R.get('decision') if not errs else 'FAIL_INTEGRITY','result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest(),'families_checked':len(expected)}
(ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
raise SystemExit(0 if not errs else 2)
