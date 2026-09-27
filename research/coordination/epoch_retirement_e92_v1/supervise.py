from pathlib import Path
import json,subprocess,sys,time
source=Path(__file__).resolve().parent
phase=sys.argv[1]; index=int(sys.argv[2]); root=source/phase
root.mkdir(exist_ok=True)
receipt=root/f'launch-{index}.json'
if receipt.exists(): raise SystemExit('refuse repeated batch')
argv=[sys.executable,'-S','-B',str(source/'experiment.py'),'batch',str(root),str(index),phase]
start=time.monotonic_ns(); p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
timed=False
try: out,err=p.communicate(timeout=30)
except subprocess.TimeoutExpired:
 timed=True; p.kill();out,err=p.communicate()
r={'argv':argv,'pid':p.pid,'exit':p.returncode,'timed_out':timed,'start_ns':start,'end_ns':time.monotonic_ns(),'stdout':out.decode(),'stderr':err.decode()}
receipt.write_text(json.dumps(r,sort_keys=True)+'\n')
print(json.dumps({'phase':phase,'batch':index,'exit':p.returncode,'timed_out':timed,'stderr':r['stderr']}))
raise SystemExit(0 if p.returncode==0 and not timed else 1)
