import json,subprocess,sys,hashlib
from pathlib import Path
p=Path('/src/runtime.pyz')
a=subprocess.run([sys.executable,str(p),'--help'],capture_output=True,text=True)
b=subprocess.run([sys.executable,str(p),'doctor','--check-dependencies'],capture_output=True,text=True)
print(json.dumps({'archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'python':sys.version,'help_exit':a.returncode,'help':a.stdout,'doctor_exit':b.returncode,'doctor':b.stdout,'stderr':a.stderr+b.stderr}))
raise SystemExit(a.returncode or b.returncode)
