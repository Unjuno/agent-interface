#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
ORDER=[0,12,2,8,1,4]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    rows=[]; complete=True
    for p in ORDER:
        d=a.root/f'{p:02d}ms'
        needed=[d/'report.json',d/'score.json',d/'execution'/'execution.json',d/'executor.exitcode',d/'scorer.exitcode']
        missing=[str(x.relative_to(a.root)) for x in needed if not x.exists()]
        if missing:
            complete=False; rows.append({'pacing_ms':p,'complete':False,'missing':missing,'eligible':False}); continue
        rep=json.loads((d/'report.json').read_text()); score=json.loads((d/'score.json').read_text()); ex=json.loads((d/'execution'/'execution.json').read_text())
        stale=ex.get('stale',{})
        eligible=all([rep.get('executor_exitcode')==0,rep.get('scorer_exitcode')==0,rep.get('passed') is True,score.get('passed') is True,len(score.get('mismatches',[]))==0,ex.get('release_verified') is True,stale.get('accepted') is False,stale.get('error')=='STALE_OBSERVATION',stale.get('emissions_before')==stale.get('emissions_after')])
        rows.append({'pacing_ms':p,'complete':True,'eligible':eligible,'mismatch_count':len(score.get('mismatches',[])),'mismatches':score.get('mismatches',[]),'task_elapsed_ns':ex.get('task_elapsed_ns'),'backend_emissions':ex.get('backend_emissions'),'release_verified':ex.get('release_verified'),'output_sha256':rep.get('output_sha256')})
    passing=sorted(r['pacing_ms'] for r in rows if r.get('eligible'))
    out={'schema':'agent-interface/office-x11-text-pacing-formal-v1','fixed_order':ORDER,'complete':complete,'rows':rows,'minimum_eligible_tested_ms':passing[0] if passing else None,'disposition':'PASS_MINIMUM_TESTED' if complete and passing else ('UNCERTAIN_INCOMPLETE' if not complete else 'FAIL_NO_ELIGIBLE')}
    a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); return 0 if out['disposition']=='PASS_MINIMUM_TESTED' else 1
if __name__=='__main__': raise SystemExit(main())
