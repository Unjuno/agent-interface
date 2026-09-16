"""Materialize new ID002 only; do not run any measurement. Preserve ID001 unchanged."""
import hashlib,json,sys
from pathlib import Path
import bootstrap
TASK='QUIET-WATCH-LIVE-PLACEMENT-20260916-002'
PLAN_SHA256='9168aec3fd7fb0074600b43121b906fd53968bd4830a7df83a23603a4da856fe'
FREEZE_SHA256='cde4f29b43aee75c65a231dee364c7110c0463ccfd321a8ecee464fcfb873e60'
def materialize(destination):
    bootstrap.unpack(destination)
    p=Path(destination)
    plan=json.loads((p/'plan.json').read_text());plan['task']=TASK
    (p/'plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
    freeze=json.loads((p/'freeze.json').read_text());freeze['task']=TASK
    freeze['sources']['plan.json']=hashlib.sha256((p/'plan.json').read_bytes()).hexdigest()
    (p/'freeze.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    if freeze['sources']['plan.json']!=PLAN_SHA256:raise ValueError('repair plan mismatch')
    if hashlib.sha256((p/'freeze.json').read_bytes()).hexdigest()!=FREEZE_SHA256:raise ValueError('repair freeze mismatch')
    return {'task':TASK,'source_changes':['plan.json task identity only'],'changed_gates':False,'changed_schedule':False}
if __name__=='__main__':print(json.dumps(materialize(sys.argv[1]),sort_keys=True))
