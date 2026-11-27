import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
label=sys.argv[1]
cmd=sys.argv[2:]
out=root/label
out.mkdir(exist_ok=False)
start=time.time_ns()
record={'argv':cmd,'cwd':str(root),'started_wall_ns':start,'supervisor_pid':os.getpid(),'timeout_seconds':150}
with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
 try:
  p=subprocess.Popen(cmd,cwd=root,stdout=stdout,stderr=stderr)
  record['child_pid']=p.pid
  (out/'started.json').write_text(json.dumps(record,indent=2)+'\n')
  try:record['returncode']=p.wait(timeout=150)
  except subprocess.TimeoutExpired:
   p.kill(); record['returncode']=p.wait();record['timeout']=True
 except Exception as e:record.update(error=repr(e),returncode=None)
record['finished_wall_ns']=time.time_ns()
(out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
