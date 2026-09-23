"""Real private socket + Mindustry focus interruption; scripted, not model timing."""
import hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from unix_json_deadline import exchange
from stopped_client_v1 import PendingAction
root=HERE/'results/mindustry-socket-focus-01';root.mkdir()
run=root/'runtime'
names=['mindustry_socket_v1.py','mindustry_focus_fixture_v1.py','mindustry_bend_interactive_v2.py','probe_mindustry_socket_focus_v1.py']
(root/'plan.json').write_text(json.dumps({'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},'scope':'scripted actual GUI focus transfer; no game task success or model latency claim'},indent=2)+'\n')
p=subprocess.Popen([sys.executable,str(HERE/'mindustry_socket_v1.py'),'--focus-fixture','serve','--','--root','/home/taka/agent-interface-bench-feasibility','--out',str(run)],stdout=subprocess.PIPE,stderr=(root/'stderr.txt').open('w'),text=True)
cursor=0;calls=[];tracker=None

def query(events,command=None,action=None,timeout=2):
 global cursor
 q={'after':cursor,'events':events,'timeout':timeout}
 if command:q.update(command=command,request_id=uuid.uuid4().hex)
 if action:q['action_id']=action
 started=time.perf_counter_ns();r=exchange(endpoint['socket'],q,timeout=timeout+3)
 calls.append({'request':q,'reply':r,'started_ns':started,'returned_ns':time.perf_counter_ns()})
 (root/'calls.json').write_text(json.dumps(calls,indent=2)+'\n')
 if tracker is not None and tracker.terminal is None:
  view=tracker.ingest(cursor,r)
  with (root/'states.jsonl').open('a') as f:f.write(json.dumps(view)+'\n')
 cursor=r.get('cursor',cursor);return r
try:
 endpoint=json.loads(p.stdout.readline());(root/'endpoint.json').write_text(json.dumps(endpoint))
 query(['observation'],timeout=30)
 r=query(['clock'],{'op':'clock'});clock=next(e for e in r['records'] if e['event']=='clock')
 tracker=PendingAction('focus-drag',cursor)
 r=query(['input_stopped','terminal'],{'op':'submit','id':'focus-drag','expected_sequence':clock['sequence'],'valid_until_ns':clock['runtime_ns']+30_000_000_000,'steps':[{'op':'pointer_drag','points':[{'x':900,'y':300},{'x':1000,'y':300}],'duration_ms':5000},{'op':'pointer_click','x':1008,'y':578,'duration_ms':80}]},'focus-drag')
 for _ in range(10):
  if tracker.terminal is not None:break
  query(['terminal'],action='focus-drag')
 assert tracker.uncertainty is None and tracker.stopped is not None,tracker.view()
 assert tracker.terminal['status']=='needs_decision' and tracker.terminal['decision_reason']=='focus_changed',tracker.view()
 r=query(['clock'],{'op':'clock'});clock=next(e for e in r['records'] if e['event']=='clock')
 r=query(['terminal'],{'op':'submit','id':'observe-recovery','expected_sequence':clock['sequence'],'valid_until_ns':clock['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]},'observe-recovery')
 assert any(e['event']=='terminal' and e['status']=='completed' for e in r['records'])
 r=query(['independent_evaluation'],{'op':'finish'},timeout=20)
 assert any(e['event']=='independent_evaluation' and e['contract_satisfied'] is False for e in r['records'])
 code=p.wait(timeout=30);assert code==0
 (root/'result.json').write_text(json.dumps({'exit_code':code,'tracker':tracker.view(),'calls':len(calls),'scope':'focus remains on fixture sink during recovery; observe-only, no game refocus claim'},indent=2)+'\n')
 print(json.dumps({'exit_code':code,'calls':len(calls),'state':tracker.view()['state']}))
finally:
 if p.poll() is None:
  try:query(['independent_evaluation'],{'op':'finish'},timeout=20);p.wait(timeout=30)
  except Exception:p.terminate();p.wait(timeout=10)
