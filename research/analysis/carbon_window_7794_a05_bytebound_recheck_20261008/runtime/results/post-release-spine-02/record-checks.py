import json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent;out={}
for name,args in [('normal',[sys.executable,str(p/'verify.py')]),('optimized',[sys.executable,'-O',str(p/'verify.py')]),('controls',[sys.executable,str(p/'controls.py')])]:
 r=subprocess.run(args,text=True,capture_output=True);out[name]={'command':args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
 if r.returncode:raise RuntimeError(name+' failed')
with (p/'verification-results.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v['returncode'] for k,v in out.items()}))
