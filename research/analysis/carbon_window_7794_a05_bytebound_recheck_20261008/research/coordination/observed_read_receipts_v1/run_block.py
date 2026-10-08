#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
plan=json.loads((HERE/'plan.json').read_text())
out=Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=False)
rows=[]
for c in plan['cases']:
    case=out/c['case_id']
    r=subprocess.run([sys.executable,str(HERE/'run_case.py'),'--case-id',c['case_id'],'--policy',c['policy'],'--scenario',c['scenario'],'--out',str(case)],text=True,capture_output=True)
    if r.returncode: raise SystemExit(f"case {c['case_id']} failed: {r.stderr}")
    rows.append(json.loads((case/'result.json').read_text()))
summary={'task':plan['task'],'allocation':plan['allocation'],'rerun_budget':plan['rerun_budget'],'rows':rows}
(out/'result.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps({'rows':len(rows)}))
