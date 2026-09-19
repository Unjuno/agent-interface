from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIX=ROOT/'fixture.json'
OUT=ROOT/'RESULT.json'
MEAS={1,2,3,4,5,6,7,8,14}
LIFE={9,10,11,12,13}

def main():
    if OUT.exists(): raise SystemExit('formal output already exists; rerun forbidden')
    f=json.loads(FIX.read_text())
    cells=f['cells']
    integrity=(len(cells)==14 and [c['id'] for c in cells]==list(range(1,15)) and len(f['sources'])==8)
    status={c['id']:bool(c['passed']) for c in cells}
    measurement=all(status[i] for i in MEAS)
    lifecycle=all(status[i] for i in LIFE)
    if not integrity: decision='FAIL_INTEGRITY'
    elif not measurement: decision='HOLD_MINDUSTRY_MEASUREMENT_PREREQ_MISSING'
    elif not lifecycle: decision='HOLD_MINDUSTRY_COMPOSED_LIFECYCLE_MISSING'
    else: decision='PASS_MINDUSTRY_SECOND_DOMAIN_READY_SCOPED'
    missing=[c['id'] for c in cells if not c['passed']]
    blocker='none' if not missing else ('composed_persistent_lifecycle' if set(missing)<=LIFE else 'measurement_or_correctness_prerequisite')
    out={'schema':'mindustry_second_domain_readiness_result_v1','task':f['task'],'base':f['base'],
         'formal_invocation':1,'formal_reruns':0,'decision':decision,'integrity_ok':integrity,
         'measurement_prereqs_pass':measurement,'composed_lifecycle_pass':lifecycle,
         'missing_cells':missing,'blocker_class':blocker,'cells':cells,'source_git_blobs':f['sources'],
         'next_if_composed_hold':'model-free/source-first Mindustry integrated mechanics preflight; freeze one repeat workload and cold/reuse/invalidation/repair/reuse control flow before any model allocation',
         'scope':'retained-evidence closure only; no live/model/GUI/Mindustry performance result'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'missing_cells':missing,'blocker_class':blocker},indent=2))
if __name__=='__main__': main()
