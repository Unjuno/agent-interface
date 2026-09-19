import json,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    for i in range(3):
        d=root/f'arm-{i:02d}';d.mkdir();(d/'result.json').write_text(json.dumps({'decision':'HARNESS_FAIL','startup':True,'input_operations':0,'error':'synthetic'}))
    (root/'summary.json').write_text(json.dumps({'decision':'HARNESS_FAIL','input_operations':0}))
    p=subprocess.run([sys.executable,str(HERE/'audit.py'),str(root),'--plan',str(HERE/'plan.json')],capture_output=True,text=True)
    assert p.returncode==0,(p.stdout,p.stderr)
    assert json.loads(p.stdout)['decision']=='HARNESS_FAIL'
print('PASS_TYPED_HARNESS_AUDIT')
