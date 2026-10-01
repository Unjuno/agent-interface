#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys
HERE=Path(__file__).resolve().parent; plan=json.loads((HERE/'plan.json').read_text()); out=Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=False); rows=[]
for c in plan['cases']:
    d=out/c['case_id']; r=subprocess.run([sys.executable,str(HERE/'run_case.py'),'--case-id',c['case_id'],'--mode',c['mode'],'--scenario',c['scenario'],'--out',str(d)],capture_output=True,text=True)
    if r.returncode: raise SystemExit(f"case {c['case_id']} failed: {r.stderr}")
    rows.append(json.loads((d/'result.json').read_text()))
(out/'result.json').write_text(json.dumps({'task':plan['task'],'allocation':plan['allocation'],'rerun_budget':plan['rerun_budget'],'rows':rows},indent=2,sort_keys=True)+'\n'); print(json.dumps({'rows':len(rows)}))
