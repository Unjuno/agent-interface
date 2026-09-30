import copy
import json
import subprocess
import sys
from pathlib import Path

src=Path('/src'); out=Path('/out'); baseline=json.loads((out/'formal01/result.json').read_bytes())
mutations={
    'wrong_proposal':lambda d: d['rows'][0]['proposal']['arguments'].__setitem__('target','delete_workspace'),
    'wrong_case_count':lambda d: d.__setitem__('case_count',8),
    'active_mutated':lambda d: d.__setitem__('invalid_candidate_preserved_active',False),
    'wrong_effect':lambda d: d['rows'][0]['effect'].__setitem__('email_reminders',False),
}
rows=[]
for name, mutate in mutations.items():
    candidate=copy.deepcopy(baseline); mutate(candidate)
    path=out/(name+'.json'); path.write_text(json.dumps(candidate,sort_keys=True,indent=2)+'\n')
    cp=subprocess.run([sys.executable,'-B',str(src/'audit.py'),str(path)],capture_output=True,text=True)
    try: report=json.loads(cp.stdout)
    except Exception: report={"errors":["INVALID_AUDITOR_OUTPUT"],"decision":"FAIL"}
    rows.append({"name":name,"rejected":cp.returncode==1 and report.get('decision')=='FAIL' and bool(report.get('errors')) and cp.stderr=='' and path.read_bytes()!= (out/'formal01/result.json').read_bytes(),"exit":cp.returncode,"errors":report.get('errors'),"stderr":cp.stderr})
result={"schema":"issue4680-independent-audit-corruption-controls-v1","count":len(rows),"rejected":sum(r['rejected'] for r in rows),"rows":rows}
(out/'controls.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
raise SystemExit(0 if result['rejected']==len(mutations) else 1)

