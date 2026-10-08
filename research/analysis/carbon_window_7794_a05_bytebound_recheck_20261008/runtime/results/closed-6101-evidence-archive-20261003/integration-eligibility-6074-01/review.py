"""New API-boundary review; never executes or alters the frozen T0 corpus."""
from pathlib import Path
import importlib.util, json, hashlib
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('reviewed_candidate',root/'candidate.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
controls=[
    ('unsupported_predicate',dict(predicate='unsupported_effect',value_interval=[0,1],coverage='complete',identity='bound')),
    ('reversed_interval',dict(predicate='distance_le_12',value_interval=[14,10],coverage='complete',identity='bound')),
    ('boolean_measurement',dict(predicate='distance_le_12',value_interval=[True,True],coverage='complete',identity='bound')),
    ('unsupported_duration_complete',dict(predicate='duration_inside_12',value_interval=[0,1],coverage='complete',identity='bound')),
]
rows=[]
for name,case in controls:
    try: result=module.classify(case)
    except Exception as error: result={'exception':type(error).__name__}
    rows.append(dict(control=name,input=case,actual=result,expected='UNKNOWN_OR_TYPED_REFUSAL',eligible=result=='UNKNOWN' or isinstance(result,dict)))
report=dict(source_pr=6090,source_head='05450a2f6d3c529d048a52c3df44a28c9cbc73e0',source_sha256=hashlib.sha256((root/'candidate.py').read_bytes()).hexdigest(),scope='new integration boundary controls; no original corpus rerun; no GUI/model or calibrated measurement',rows=rows,disposition='HOLD_RUNTIME_INTEGRATION' if not all(r['eligible'] for r in rows) else 'BOUNDARY_CONTROLS_PASS')
(root/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
