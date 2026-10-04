"""File-mediated model proposals on actual OpenTTD with fresh admission."""
import hashlib, json, subprocess, sys, tempfile, time, shutil, os
from pathlib import Path
from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
HERE=Path(__file__).resolve().parent
root=HERE/'results/timing-envelope-openttd-03';root.mkdir(exist_ok=False)
def dump(name,value):
 path=root/name;temp_path=path.with_suffix(path.suffix+'.tmp');temp_path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temp_path,path)
names=['timing_envelope_openttd_driver_v3.py','durable_submit_v4.py','append_checkpoint_v1.py','received_continuation_v1.py','received_exchange_v2.py','pointer_socket_entry_v2.py','event_socket_v11.py','model_pair_runner_v1.py','openttd_proposal_schema_v3.py','timing_envelope_openttd_supervisor_v3.py','timing_envelope_v1.py','timing_envelope_v2.py','session_v10.py']
dump('plan.json',{'seed_semantics':'canonical save; no RNG override','scope':'fresh typed OpenTTD task with buffered supervisor TimingEnvelope v2',
     'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,'-u',str(HERE/'pointer_socket_entry_v2.py'),'openttd','serve','--',
                    '--root','/home/taka/agent-interface-bench-feasibility',
                    '--out',str(root/'runtime'),'--controller','assistant'],
                   stdout=subprocess.PIPE,stderr=(root/'stderr.txt').open('w'),text=True)
temp=tempfile.TemporaryDirectory(prefix='agent-interface-live-openttd-');journal=Path(temp.name)/'journal.jsonl';calls=[]
try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep)
 initial=request_once(ep['socket'],start(ep['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial)
 initialize(journal,initial['continuation'])
 task=next(e['task'] for e in initial['reply']['records'] if e['event']=='ready')
 dump('ready.json',{'task':task,'observation':initial['continuation']['observation'],'bridge_pid':p.pid})
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
   if (root/'abort.json').exists():path=root/'abort.json';break
   assert p.poll() is None,'bridge exited while waiting for model'
   if time.monotonic()>deadline:raise TimeoutError('proposal wait limit; no automatic input')
   time.sleep(.05)
  proposal=json.loads(path.read_text(encoding='utf-8'));received=time.perf_counter_ns()
  if proposal.get('finish') is True:
   state=load(journal)['continuation']
   finish=request_once(ep['socket'],state,{'events':['independent_evaluation'],'timeout':25,'command':{'op':'finish'},'request_id':'finish-once'})
   dump('finish.json',finish);code=p.wait(timeout=10);assert code==0
   evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation')
   assert evaluation['contract_satisfied'] is True
   dump('result.json',{'exit_code':code,'proposals_executed':index-1,'journal_calls':len(calls),'scope':'typed model proposals automatically passed through isolated OpenTTD supervisor'})
   break
  steps=proposal['steps'];assert type(steps) is list and 1<=len(steps)<=6
  assert all(s.get('op') in ('pointer_move','pointer_click','pointer_drag','observe','dwell_observe') for s in steps)
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
