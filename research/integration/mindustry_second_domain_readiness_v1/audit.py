from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MEAS={1,2,3,4,5,6,7,8,14}; LIFE={9,10,11,12,13}

def main():
    f=json.loads((ROOT/'fixture.json').read_text()); r=json.loads((ROOT/'RESULT.json').read_text())
    cells=f['cells']; status={int(c['id']):bool(c['passed']) for c in cells}
    checks={}
    checks['cell_identity']=[c['id'] for c in cells]==list(range(1,15))
    checks['source_count']=len(f['sources'])==8 and f['sources']==r['source_git_blobs']
    checks['measurement']=all(status[i] for i in MEAS)==r['measurement_prereqs_pass']==True
    checks['lifecycle']=all(status[i] for i in LIFE)==r['composed_lifecycle_pass']==False
    checks['missing']=[i for i in range(1,15) if not status[i]]==r['missing_cells']==[9,11,12,13]
    checks['blocker']=r['blocker_class']=='composed_persistent_lifecycle'
    expected=('FAIL_INTEGRITY' if not (checks['cell_identity'] and checks['source_count']) else
              'HOLD_MINDUSTRY_MEASUREMENT_PREREQ_MISSING' if not all(status[i] for i in MEAS) else
              'HOLD_MINDUSTRY_COMPOSED_LIFECYCLE_MISSING' if not all(status[i] for i in LIFE) else
              'PASS_MINDUSTRY_SECOND_DOMAIN_READY_SCOPED')
    checks['decision']=r['decision']==expected
    checks['formal_count']=r['formal_invocation']==1 and r['formal_reruns']==0
    passed=all(checks.values())
    out={'schema':'mindustry_second_domain_readiness_audit_v1','passed':passed,'checks':checks,
         'decision':r['decision'],'result_sha256':hashlib.sha256((ROOT/'RESULT.json').read_bytes()).hexdigest()}
    (ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2))
    raise SystemExit(0 if passed else 1)
if __name__=='__main__': main()
