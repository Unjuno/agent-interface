#!/usr/bin/env python3
import copy, json
from pathlib import Path
from common import validate_fixture, compute
R=Path(__file__).resolve().parent
base=json.loads((R/'fixture.json').read_text())
controls=[]
def attempt(name, mutate):
    f=copy.deepcopy(base); mutate(f)
    rejected=False
    try: validate_fixture(f); compute(f)
    except Exception: rejected=True
    controls.append({'name':name,'rejected':rejected})
attempt('denominator_substitution_plain', lambda f: f['primary_comparator'].__setitem__('denominator_id','plain.task4.layout_B.cold'))
attempt('repair_route_changed', lambda f: f['repair'].__setitem__('route','cold'))
attempt('layout_mismatch', lambda f: f['matched_reacquisition'].__setitem__('layout','A'))
attempt('source_blob_changed', lambda f: f['source'].__setitem__('git_blob','0'*40))
attempt('repeat_B_model_call_injected', lambda f: f['persistent_repeat_B'].__setitem__('planner_generations',1))
out={'schema':'integrated_efficiency_repair_reacquisition_corruption_v1','all_rejected':all(x['rejected'] for x in controls),'controls':controls}
(R/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True))
raise SystemExit(0 if out['all_rejected'] else 1)
