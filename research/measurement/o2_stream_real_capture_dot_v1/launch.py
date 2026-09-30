"""One-shot bounded local supervisor; no external jobs or services."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('--construction',action='store_true');a=p.parse_args()
if Path(a.out).name!=a.out:raise SystemExit('output must be one local basename')
if (ROOT/a.out).exists():raise SystemExit('STOP output exists')
if not a.construction:
 freeze=json.loads((ROOT/'FREEZE.json').read_text())
 for name,expected in freeze['sha256'].items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise SystemExit('STOP freeze mismatch '+name)
with (ROOT/(a.out+'.started')).open('x',encoding='utf-8') as f:f.write(str(time.time_ns())+'\n')
command=[sys.executable,'-B','run.py','--out',a.out]+(['--construction'] if a.construction else [])
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
started=time.time_ns();timed_out=False
try:
 r=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
 code=r.returncode;stdout=r.stdout;stderr=r.stderr
except subprocess.TimeoutExpired as e:
 timed_out=True;code=None;stdout=e.stdout or b'';stderr=e.stderr or b''
ended=time.time_ns()
for suffix,data in [('stdout',stdout),('stderr',stderr)]:
 with (ROOT/(a.out+'.'+suffix)).open('xb') as f:f.write(data)
receipt={'command':command,'cwd':str(ROOT),'started_unix_ns':started,'ended_unix_ns':ended,'actual_exit':code,'timed_out':timed_out,'timeout_seconds':30,'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()}
with (ROOT/(a.out+'.launch.json')).open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
print(json.dumps(receipt));sys.exit(124 if timed_out else code)
