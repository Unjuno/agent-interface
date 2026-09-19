"""Two-stage real-observation/model boundary probe; no arbitrary model commands."""
import hashlib,json,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from unix_json_deadline import exchange
from focus_decision_view_v2 import build
from menu_intent_guard_v2 import check
from PIL import Image
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
 dump('plan.json',{'scope':'live bounded known-menu intent; single click after new observation and exact patch check','sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('live_menu_intent_v3.py','focus_decision_view_v2.py','mindustry_socket_v1.py','menu_intent_guard_v1.py','menu_intent_guard_v2.py','mindustry_menu_mutation_fixture_v2.py','mindustry_menu_mutation_socket_v2.py')}})
 query(['observation'],timeout=30);c=clock();reply=observe('model-observation',c);view=build(reply);c=clock()
 age=(c['runtime_ns']-view['observation']['capture_ns'])/1e6
 state.update(source_observation=view['observation'],prepared_clock=c);dump('state.json',state)
 evidence={'measurement_age_ms':age,'max_age_ms':1000,'target_focus':view['observation']['input_focus_after'],'evidence':view}
 prompt='The user requests selecting the basic Conveyor menu item in this private Mindustry fixture, once. No construction or other action is requested. Do not use tools, files, commands or browsing. No image is attached. Return only JSON {"intent":"select_basic_conveyor","execute_once":true}. This is a bounded proposal only: the runtime must acquire a new observation, verify the known menu patch and original target binding, enforce its fresh deadline and reject any mismatch; no retry. Historical evidence:\n'+json.dumps(evidence,sort_keys=True,separators=(',',':'))
 (root/'prompt.txt').write_bytes(prompt.encode());dump('prepared.json',{'age_ms':age,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'runtime_clock_ns':c['runtime_ns'],'source_capture_ns':view['observation']['capture_ns']})
 print(json.dumps({'prepared_age_ms':age,'sequence':view['observation']['sequence']}))
elif stage=='revalidate':
 lines=[json.loads(l) for l in (root/'model/events.jsonl').read_text().splitlines()]
 answer=json.loads(next(e['item']['text'] for e in lines if e['type']=='item.completed' and e['item']['type']=='agent_message'))
 c=clock();old_age=(c['runtime_ns']-state['source_observation']['capture_ns'])/1e6
 reply=observe('intent-revalidation',c)
 fresh=next(e for e in reversed(reply['records']) if e['event']=='observation')
 c=clock()
 with Image.open(state['source_observation']['image']) as source_image,Image.open(fresh['image']) as fresh_image:
  guard=check(answer,state['source_observation'],fresh,source_image,fresh_image,c['runtime_ns'])
 decision={'model_answer':answer,'old_observation_age_ms':old_age,'fresh_observation':fresh,'revalidation_clock_ns':c['runtime_ns'],'guard':guard}
 dump('decision.json',decision)
 if guard['eligible']:
  action=query(['terminal'],{'op':'submit','id':'execute-menu-intent','expected_sequence':fresh['sequence'],'valid_until_ns':guard['valid_until_ns'],'steps':[{'op':'pointer_click','x':guard['point'][0],'y':guard['point'][1],'duration_ms':80},{'op':'observe'}]})
  dump('action.json',action)
 result=query(['independent_evaluation'],{'op':'finish'},timeout=20)
 for _ in range(5):
  if any(e['event']=='independent_evaluation' for e in result['records']):break
  result=query(['independent_evaluation'],timeout=2)
 assert any(e['event']=='independent_evaluation' for e in result['records'])
 print(json.dumps(decision))
else:raise ValueError(stage)
