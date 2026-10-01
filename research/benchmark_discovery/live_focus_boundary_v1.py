"""Two-stage real-observation/model boundary probe; no arbitrary model commands."""
import hashlib,json,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from unix_json_deadline import exchange
from focus_decision_view_v2 import build
stage,socket,output=sys.argv[1:];root=Path(output);statepath=root/'state.json'
state=json.loads(statepath.read_text()) if statepath.exists() else {'cursor':0,'calls':[]}
def dump(name,value):(root/name).write_text(json.dumps(value,indent=2)+'\n')
def query(events,command=None,timeout=2):
 q={'after':state['cursor'],'events':events,'timeout':timeout}
 if command:q.update(command=command,request_id=uuid.uuid4().hex)
 start=time.perf_counter_ns();r=exchange(socket,q,timeout=timeout+3);end=time.perf_counter_ns()
 state['calls'].append({'request':q,'reply':r,'started_ns':start,'returned_ns':end});state['cursor']=r['cursor'];dump('state.json',state)
 return r

def clock():
 return next(e for e in query(['clock'],{'op':'clock'})['records'] if e['event']=='clock')
def observe(identifier,c):
 return query(['terminal'],{'op':'submit','id':identifier,'expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]})
if stage=='prepare':
 dump('plan.json',{'scope':'live text-only model-boundary staleness probe; 1000ms experimental budget, no game inputs','sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('live_focus_boundary_v1.py','focus_decision_view_v2.py','mindustry_socket_v1.py')}})
 query(['observation'],timeout=30);c=clock();reply=observe('model-observation',c);view=build(reply);c=clock()
 age=(c['runtime_ns']-view['observation']['capture_ns'])/1e6
 state.update(source_observation=view['observation'],prepared_clock=c);dump('state.json',state)
 evidence={'measurement_age_ms':age,'max_age_ms':1000,'target_focus':view['observation']['input_focus_after'],'evidence':view}
 prompt='''Read this historical live interface observation; no tools, files, browsing or commands. No image attached. Return only JSON with observed_target_binding (boolean), proposal (observe_only if measurement_age_ms exceeds max_age_ms, otherwise propose_new_target_action when latest pointer_binding focus/surface match target_focus, else propose_focus_recovery), automatic_tail_replay (always false), reuse_old_lease (always false), runtime_revalidation_required (always true). The age is measured at prompt preparation; time may pass during your response. Your proposal is not executable authority.\n'''+json.dumps(evidence,sort_keys=True,separators=(',',':'))
 (root/'prompt.txt').write_bytes(prompt.encode());dump('prepared.json',{'age_ms':age,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'runtime_clock_ns':c['runtime_ns'],'source_capture_ns':view['observation']['capture_ns']})
 print(json.dumps({'prepared_age_ms':age,'sequence':view['observation']['sequence']}))
elif stage=='revalidate':
 lines=[json.loads(l) for l in (root/'model/events.jsonl').read_text().splitlines()]
 answer=json.loads(next(e['item']['text'] for e in lines if e['type']=='item.completed' and e['item']['type']=='agent_message'))
 assert answer['automatic_tail_replay'] is False and answer['reuse_old_lease'] is False and answer['runtime_revalidation_required'] is True
 c=clock();age=(c['runtime_ns']-state['source_observation']['capture_ns'])/1e6
 decision={'model_answer':answer,'revalidation_clock_ns':c['runtime_ns'],'source_capture_ns':state['source_observation']['capture_ns'],'revalidated_age_ms':age,'max_age_ms':1000,'dispatch':'observe_only' if age>1000 else 'fresh_intent_required','model_receipt_ns':None,'scope':'same runtime clock for image age; model output not input authority'}
 dump('decision.json',decision)
 if age>1000:observe('stale-reobservation',c)
 result=query(['independent_evaluation'],{'op':'finish'},timeout=20)
 for _ in range(5):
  if any(e['event']=='independent_evaluation' for e in result['records']):break
  result=query(['independent_evaluation'],timeout=2)
 assert any(e['event']=='independent_evaluation' for e in result['records'])
 print(json.dumps(decision))
else:raise ValueError(stage)
