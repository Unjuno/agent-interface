import json
import subprocess
import sys
from pathlib import Path

src=Path('/src'); out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
steps=[
    ('construction_tests',[sys.executable,'-B','-m','unittest','discover','-s',str(src),'-p','test_skill_package.py','-v']),
    ('formal_runner',[sys.executable,'-B',str(src/'run.py'),str(out/'formal01')]),
    ('independent_audit',[sys.executable,'-B',str(src/'audit.py'),str(out/'formal01/result.json')]),
    ('corruption_controls',[sys.executable,'-B',str(src/'controls.py')]),
]
records=[]
for name,argv in steps:
    cp=subprocess.run(argv,cwd=src,capture_output=True,timeout=30)
    (out/(name+'.stdout')).write_bytes(cp.stdout)
    (out/(name+'.stderr')).write_bytes(cp.stderr)
    if name=='independent_audit' and cp.returncode==0:
        (out/'formal01/audit.json').write_bytes(cp.stdout)
    records.append({'name':name,'argv':argv,'exit_code':cp.returncode})
    if cp.returncode!=0:
        (out/'execution.json').write_text(json.dumps({'steps':records},indent=2)+'\n')
        raise SystemExit(cp.returncode)
final=json.loads((out/'formal01/audit.json').read_bytes())
controls=json.loads((out/'controls.json').read_bytes())
ok=final.get('decision')=='PASS_CONSTRUCTION_SCOPED' and final.get('errors')==[] and controls.get('rejected')==4
(out/'execution.json').write_text(json.dumps({'steps':records,'audit_decision':final.get('decision'),'audit_errors':final.get('errors'),'corruption_controls_rejected':controls.get('rejected'),'success':ok},indent=2)+'\n')
print((out/'execution.json').read_text(),end='')
raise SystemExit(0 if ok else 1)

