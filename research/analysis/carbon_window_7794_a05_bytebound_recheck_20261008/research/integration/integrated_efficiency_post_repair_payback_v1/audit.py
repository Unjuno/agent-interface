import json
from decimal import Decimal
from pathlib import Path
from common import compute, MODEL_KEYS
ROOT=Path(__file__).resolve().parent
f=json.loads((ROOT/'fixture.json').read_text())
r=json.loads((ROOT/'RESULT.json').read_text())
p,e,diffs,ratios=compute(f)
checks={}
checks['source']=r['source_git_blob']==f['source_git_blob']
checks['phases']=r['horizon_phases']==['layout_change','repeat_B']
checks['persistent']=r['persistent']=={k:(str(v) if k=='elapsed_ms' else v) for k,v in p.items()}
checks['ephemeral']=r['ephemeral']=={k:(str(v) if k=='elapsed_ms' else v) for k,v in e.items()}
checks['diffs']=r['persistent_minus_ephemeral']==diffs
checks['ratios']=r['persistent_over_ephemeral']==ratios
checks['repeat_zero']=all(r['repeat_B_persistent'][k]==0 for k in MODEL_KEYS)
checks['wall']=Decimal(r['persistent']['elapsed_ms']) < Decimal(r['ephemeral']['elapsed_ms'])
checks['model']=all(r['persistent'][k] < r['ephemeral'][k] for k in MODEL_KEYS)
checks['formal']=r['formal_invocation']==1 and r['reruns']==0
checks['decision']=r['decision']=='PASS_POST_REPAIR_REUSE_PAYBACK_RECONSTRUCTED_SCOPED'
passed=all(checks.values())
out={'schema':'integrated_efficiency_post_repair_payback_audit_v1','passed':passed,'checks':checks,'decision':r['decision']}
(ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if not passed: raise SystemExit(1)
print(json.dumps(out, sort_keys=True))
