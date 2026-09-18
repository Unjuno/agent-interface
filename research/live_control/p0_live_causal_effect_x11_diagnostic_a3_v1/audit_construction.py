from __future__ import annotations
import argparse,json
from pathlib import Path

STOP='PREFORMAL_SETUP_STOP_EFFECT_CHILD_DIAGNOSED'
ELIGIBLE='CONSTRUCTION_ELIGIBLE_FOR_FROZEN_FORMAL'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());errors=[]
    if r.get('task')!='P0-LIVE-CAUSAL-EFFECT-X11-DIAGNOSTIC-A3-20260918-003':errors.append('task')
    if r.get('phase')!='construction' or r.get('formal_invocations')!=0 or r.get('reruns')!=0:errors.append('invocation')
    if r.get('science_runner_blob')!='d8c509a55fe5363dc5211aebe510a720e964f7f3':errors.append('science_source')
    rows=r.get('rows',[])
    if len(rows)!=2:errors.append('sessions')
    incomplete=[x for x in rows if x.get('science_row_present') is not True]
    diag_ok=True
    for x in rows:
        for k in ('child_status_path','supervisor_row_path'):
            p=x.get(k)
            if not p or not Path(p).exists():diag_ok=False
    if not diag_ok:errors.append('diagnostic_persistence')
    if errors:decision='FAIL_INTEGRITY'
    elif incomplete:decision=STOP
    elif r.get('summary',{}).get('science_eligible') is not True:decision='FAIL_INTEGRITY'
    else:decision=ELIGIBLE
    out={'decision':decision,'errors':errors,'pass':decision in (STOP,ELIGIBLE) and not errors,
         'sessions':len(rows),'incomplete_sessions':len(incomplete),'diagnostics_persisted':diag_ok}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
