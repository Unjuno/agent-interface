"""Actual GUI cancellation/re-observation integration probe, not agent gameplay."""
import hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
out=HERE/'results/mindustry-runtime-cancel-01'
meta=HERE/'results/mindustry-runtime-cancel-driver-01';meta.mkdir()
(meta/'plan.json').write_text(json.dumps({'scope':'scripted integration only; no gameplay success claim','driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'expected':'cancel drag, suppress tail, observe with a fresh program, empty route fails independent game score'},indent=2))
p=subprocess.Popen([sys.executable,str(HERE/'mindustry_bend_interactive_v2.py'),'--root','/home/taka/agent-interface-bench-feasibility','--out',str(out)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(meta/'stderr.txt').open('w'),text=True,bufsize=1)
q=queue.Queue();events=[]
def read():
 for line in p.stdout:
  (meta/'stdout.jsonl').open('a').write(line)
  q.put(json.loads(line))
 q.put(None)
threading.Thread(target=read,daemon=True).start()
def until(kind,identifier=None):
 deadline=time.monotonic()+90
 while True:
  e=q.get(timeout=max(.01,deadline-time.monotonic()))
  if e is None:raise RuntimeError('runtime exited before '+kind)
  events.append(e)
  if e['event']==kind and (identifier is None or e.get('id')==identifier):return e

def send(c):
 (meta/'commands.jsonl').open('a').write(json.dumps(c)+'\n');p.stdin.write(json.dumps(c)+'\n');p.stdin.flush()
try:
 initial=until('observation');send({'op':'clock'});clock=until('clock')
 send({'op':'submit','id':'cancel-drag','expected_sequence':initial['sequence'],'valid_until_ns':clock['runtime_ns']+30_000_000_000,'steps':[{'op':'pointer_drag','points':[{'x':900,'y':300},{'x':1000,'y':300}],'duration_ms':5000},{'op':'pointer_click','x':1008,'y':578,'duration_ms':80}]})
 until('step_started','cancel-drag');time.sleep(.15);send({'op':'cancel','id':'cancel-drag'});terminal=until('terminal','cancel-drag')
 assert terminal['status']=='cancelled' and terminal['release']['verified'] is True,terminal
 assert not any(e['event']=='step_started' and e.get('id')=='cancel-drag' and e['step']==1 for e in events)
 send({'op':'clock'});clock=until('clock')
 send({'op':'submit','id':'observe-recovery','expected_sequence':clock['sequence'],'valid_until_ns':clock['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]})
 recovery=until('terminal','observe-recovery');assert recovery['status']=='completed',recovery
 send({'op':'finish'});evaluation=until('independent_evaluation');assert evaluation['contract_satisfied'] is False,evaluation
 p.stdin.close();code=p.wait(timeout=30);assert code==0
 (meta/'result.json').write_text(json.dumps({'exit_code':code,'cancel_terminal':terminal,'recovery_terminal':recovery,'evaluation':evaluation,'scope':'actual GUI scripted cancellation; no focus-loss, socket recovery or gameplay success claim'},indent=2)+'\n')
 print(json.dumps({'exit_code':code,'cancel':terminal['status'],'recovery':recovery['status'],'game_score':evaluation['status']}))
finally:
 if p.poll() is None:
  p.stdin.close()
  try:p.wait(timeout=30)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
