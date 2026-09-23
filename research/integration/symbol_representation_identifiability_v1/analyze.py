from __future__ import annotations
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
LEDGER=ROOT/'LEDGER.json'; OUT=ROOT/'RESULT.json'
REQUIRED_GATES=[
'model_facing','same_task_fixture','same_underlying_semantic_evidence','same_definitions',
'same_model_effort','same_prompt_schema_except_representation','same_execution_policy',
'same_session_cache_treatment','independent_outcome_accounting','representation_only_difference',
'canonical_vs_compact_same_meaning']

def main():
    d=json.loads(LEDGER.read_text())
    rows=[]
    admissible=0
    for f in d['families']:
        g=f['gates']
        missing=[k for k in REQUIRED_GATES if k not in g]
        if missing: raise SystemExit(f'missing gates {f["id"]}:{missing}')
        failed=[k for k in REQUIRED_GATES if g[k] is not True]
        ok=not failed
        admissible += int(ok)
        rows.append({'id':f['id'],'admissible':ok,'failed_gates':failed,'reason':f['reason'],'git_blob':f['git_blob'],'path':f['path']})
    complete_negative=all((not r['admissible']) and len(r['failed_gates'])>=1 for r in rows)
    if admissible:
        decision='PASS_RETAINED_SYMBOL_REPRESENTATION_IDENTIFIABLE_SCOPED'
    elif len(rows)>=4 and complete_negative:
        decision='HOLD_NO_RETAINED_SYMBOL_REPRESENTATION_CONTRAST'
    else:
        decision='FAIL_INTEGRITY'
    out={'task':d['task'],'formal_invocations':1,'reruns':0,'family_count':len(rows),'admissible_pairs':admissible,
         'all_rejections_explained':complete_negative,'rows':rows,'decision':decision,
         'ledger_sha256':hashlib.sha256(LEDGER.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
