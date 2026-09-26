"""Capture a single child invocation and its terminal status."""
import json, subprocess, sys, time
from pathlib import Path
p=Path(sys.argv[1]); command=sys.argv[2:]
start=time.monotonic_ns()
proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
try:
 out,err=proc.communicate(timeout=35)
except subprocess.TimeoutExpired:
 proc.kill();out,err=proc.communicate()
p.parent.mkdir(parents=True,exist_ok=True)
p.with_suffix('.stdout').write_text(out)
p.with_suffix('.stderr').write_text(err)
p.with_suffix('.json').write_text(json.dumps({'argv':command,'pid':proc.pid,'returncode':proc.returncode,'started_ns':start,'ended_ns':time.monotonic_ns()},indent=2,sort_keys=True)+'\n')
print(json.dumps({'receipt':str(p.with_suffix('.json')),'returncode':proc.returncode,'stdout':out[:500],'stderr_tail':err[-500:]}))
raise SystemExit(proc.returncode)
