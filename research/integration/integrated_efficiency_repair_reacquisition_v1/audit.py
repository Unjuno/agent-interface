#!/usr/bin/env python3
import json, sys
from pathlib import Path
from common import compute, validate_fixture, UNITS
R=Path(__file__).resolve().parent
f=json.loads((R/'fixture.json').read_text()); r=json.loads((R/'RESULT.json').read_text())
checks={}
try: checks['fixture']=validate_fixture(f)
except Exception: checks['fixture']=False
exp=compute(f) if checks['fixture'] else {}
checks['decision']=r.get('decision')=='PASS_REPAIR_REACQUISITION_ACCOUNTING_SCOPED'
checks['formal']=r.get('formal_invocation')==1 and r.get('formal_reruns')==0
checks['denominator']=r.get('primary_comparator',{}).get('denominator_id')=='ephemeral.task4.layout_B.cold_reacquisition'
checks['units']=set(r.get('ratios',{}))==set(UNITS)
checks['ratios']=all(r['ratios'].get(u)==exp.get(u) for u in UNITS) if checks['units'] else False
checks['repeat_B']=all(r['persistent_repeat_B'].get(k)==0 for k in ['input_tokens','output_tokens','reasoning_output_tokens','planner_generations','model_visible_images'])
checks['no_synthetic_scalar']='aggregate_ratio' not in r and 'score' not in r
checks['source']=r.get('source_git_blob')=='7db368b2d492b5b95f5f038fb7cb5dd6b78a27a7'
out={'schema':'integrated_efficiency_repair_reacquisition_audit_v1','passed':all(checks.values()),'checks':checks,'decision':r.get('decision')}
(R/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['passed'] else 1)
