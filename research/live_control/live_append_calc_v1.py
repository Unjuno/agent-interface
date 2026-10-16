"""File-mediated model proposals on actual Calc, append journal and explicit fresh observe."""
import hashlib, json, subprocess, sys, tempfile, time, shutil
from pathlib import Path
from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
HERE=Path(__file__).resolve().parent
root=HERE/'results/live-append-calc-01';root.mkdir(exist_ok=False)
def dump(name,value):(root/name).write_text(json.dumps(value,indent=2)+'\n')
names=['live_append_calc_v1.py','durable_submit_v4.py','append_checkpoint_v1.py','received_continuation_v1.py','received_exchange_v2.py','cause_servo_socket_v7.py','model_pair_runner_v1.py']
dump('plan.json',{'seed':238,'scope':'actual screenshot model proposals manually reviewed, GUI actions through append journal, no autonomous supervisor',
     'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,str(HERE/'cause_servo_socket_v7.py'),'calc','serve','--','--app','calc','--seed','238','--out',str(root/'runtime')],stdout=subprocess.PIPE,stderr=(root/'stderr.txt').open('w'),text=True)
temp=tempfile.TemporaryDirectory(prefix='agent-interface-live-calc-');journal=Path(temp.name)/'journal.jsonl';calls=[]
try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep)
 initial=request_once(ep['socket'],start(ep['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial)
 initialize(journal,initial['continuation'])
 goal=next(e['goal'] for e in initial['reply']['records'] if e['event']=='ready')
 dump('ready.json',{'goal':goal,'observation':initial['continuation']['observation'],'bridge_pid':p.pid})
 print(json.dumps({'ready':str(root/'ready.json')}),flush=True)
 def call(spec):
  begin=time.perf_counter_ns();r=run(journal,spec);end=time.perf_counter_ns()
  calls.append({'begin_ns':begin,'end_ns':end,'result':r});dump('calls.json',calls)
  assert r['state']['pending'] is None,'read pending before any further command'
  shutil.copy2(journal,root/'journal.jsonl')
  return r
 def clock():return call({'command':{'op':'clock'},'timeout':3})['state']['last_resolution']['clock']
 for index in range(1,7):
  path=root/f'proposal-{index}.json';deadline=time.monotonic()+300
  while not path.exists():
   assert p.poll() is None,'bridge exited while waiting for model'
   if time.monotonic()>deadline:raise TimeoutError('proposal wait limit; no automatic input')
   time.sleep(.05)
  proposal=json.loads(path.read_text());received=time.perf_counter_ns()
  if proposal.get('finish') is True:
   state=load(journal)['continuation']
   finish=request_once(ep['socket'],state,{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish-once'})
   dump('finish.json',finish);code=p.wait(timeout=10);assert code==0
   dump('result.json',{'exit_code':code,'proposals_executed':index-1,'journal_calls':len(calls),'scope':'model proposals with assistant review and file handoff, not autonomous loop'})
   break
  steps=proposal['steps'];assert type(steps) is list and 1<=len(steps)<=12
  assert all(s.get('op') in ('text','key','chord','pointer_click','observe','settle') for s in steps)
  before=load(journal)['continuation']['observation'];c=clock()
  fresh=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]},'timeout':3})
  obs=fresh['state']['continuation']['observation']
  assert obs['pointer_binding']==before['pointer_binding'] and obs['input_focus_before']==obs['input_focus_after'],'binding changed; replan'
  c=clock()
  applied=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':steps+[{'op':'observe'}]},'timeout':3})
  dump(f'applied-{index}.json',{'proposal_received_ns':received,'source_observation':before,'fresh_observation':obs,'result':applied,'returned_ns':time.perf_counter_ns()})
  print(json.dumps({'applied':index,'observation':applied['state']['continuation']['observation'],'resolution':applied['state']['last_resolution']}),flush=True)
 else:raise RuntimeError('proposal limit; no implicit finish success')
finally:
 if journal.exists():shutil.copy2(journal,root/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
