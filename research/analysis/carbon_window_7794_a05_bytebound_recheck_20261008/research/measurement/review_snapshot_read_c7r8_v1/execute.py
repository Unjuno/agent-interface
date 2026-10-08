"""One synchronous invocation, exclusive marker, retained actual process exit."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
mode=sys.argv[1]
index=int(sys.argv[2]) if mode=='formal' else None
name=f'c{index}' if mode=='formal' else mode
parent=R/('formal' if mode in ('formal','controls') else 'construction')
parent.mkdir(exist_ok=True)
marker=parent/(name+'.started')
with marker.open('x') as f:f.write(str(time.time_ns())+'\n')
if mode=='formal' and index:
    prior=json.loads((parent/(f'c{index-1}.exit.json')).read_text())
    if type(prior['returncode']) is not int or prior['returncode']!=0:raise ValueError('PRIOR_INCOMPLETE')
out=parent/name
cmd=[sys.executable,'-B','-S',str(R/'worker.py'),mode]
if index is not None: cmd.append(str(index))
cmd.append(str(out))
w0=time.monotonic_ns()
p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
timeout=False
try: stdout,stderr=p.communicate(timeout=20)
except subprocess.TimeoutExpired:
    timeout=True;p.kill();stdout,stderr=p.communicate()
record={'argv':cmd,'pid':p.pid,'returncode':p.returncode,'timeout':timeout,'started_ns':w0,'ended_ns':time.monotonic_ns(),
        'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()}
(parent/(name+'.stdout')).write_bytes(stdout);(parent/(name+'.stderr')).write_bytes(stderr)
(parent/(name+'.exit.json')).write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps(record),flush=True)
if p.returncode!=0 or timeout:sys.exit(1)
