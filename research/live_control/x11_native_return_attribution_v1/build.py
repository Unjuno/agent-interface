"""Build this local probe only; no network or package installation."""
import hashlib,json,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent
cmd=['gcc','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared','-Wl,--build-id=none','native.c','-o','native.so','-lX11']
x=subprocess.run(cmd,cwd=p,text=True,capture_output=True)
r=dict(command=cmd,exitcode=x.returncode,stdout=x.stdout,stderr=x.stderr,
       compiler=subprocess.check_output(['gcc','--version'],text=True))
if x.returncode==0:r['sha256']=hashlib.sha256((p/'native.so').read_bytes()).hexdigest()
(p/'build.json').write_text(json.dumps(r,indent=2)+'\n')
if x.returncode:raise RuntimeError(r)
print(r['sha256'])
