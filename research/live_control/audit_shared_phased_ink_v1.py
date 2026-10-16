"""Replay live model-selected reconciliation and independent artifact evidence."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start,advance
from append_checkpoint_v1 import load,inspect
from durable_submit_v4 import reconcile
from recovery_view_v1 import present
H=Path(__file__).resolve().parent;R=H/'results/shared-phased-ink-01';T=R/'runtime'
sys.path.insert(0,str(H.parent/'observation_tiles'))
from tile_transport import Decoder
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n,d in read(R/'plan.json')['sources'].items():assert sha(H/n)==d
for n,d in read(T/'sources.json').items():assert sha(H.parent/n)==d
events=[json.loads(l) for l in (T/'events.jsonl').read_bytes().splitlines()];ep=read(R/'endpoint.json');state=start(ep['socket'])
def replay(c):
 global state
 q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
 state=advance(state,ep['socket'],q['after'],a);assert state==c.get('state',{}).get('continuation',c.get('continuation'))
replay(read(R/'initial.json'));calls=read(R/'calls.json');assert len(calls)>=9
for c in calls:replay(c['result'])
pending=read(R/'pending.json');before=read(R/'before-loss.json');lost=read(R/'lost-request.json');recovered=read(R/'recovered.json')
assert pending['continuation']==before['continuation']==calls[2]['result']['state']['continuation']
assert pending['pending']['request']==lost and recovered==calls[3]['result']
assert hashlib.sha256((json.dumps(lost)+'\n').encode()).hexdigest()==read(R/'loss.json')['sha256']
assert read(R/'loss.json')['received_response_bytes']==0 and read(R/'blocked.json')['transport_called'] is False
assert recovered['recovery']==present(recovered)
assert 'command' not in recovered['request'] and recovered['request']['action_id']==lost['command']['id']
p,resolution=reconcile(pending['pending'],recovered['reply']['records']);assert p is None and resolution==recovered['state']['last_resolution']
assert load(R/'journal.jsonl')==calls[-1]['result']['state'];count=inspect(R/'journal.jsonl')[1];assert count==1+2*len(calls)
replay(read(R/'finish.json'))
commands=[e['command'] for e in events if e['event']=='command'];echo=[c for c in commands if c.get('transport_request_id')==lost['request_id']];assert len(echo)==1
assert echo[0]==dict(lost['command'],transport_request_id=lost['request_id'])
assert len([e for e in events if e['event']=='accepted'])==4+sum(1+int(x['submitted'])+2*int('handoff' in x)+len(x.get('readiness',{}).get('result',{}).get('checks',[])) for x in read(R/'replans.json'))
assert sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for c in commands for s in c.get('steps',[]))==2
terms=[e for e in events if e['event']=='terminal'];assert len(terms)==len([e for e in events if e['event']=='accepted'])
assert all(t['status'] in ('completed','needs_decision','expired') and t['release']['verified'] and t['release']['keys_down']==[] and t['release']['buttons_down']==[] for t in terms)
obs=[e for e in events if e['event']=='observation'];decoder=Decoder('live-control')
for n,e in enumerate(obs,1):
 f=decoder.accept((T/f'{n:03d}.ait').read_bytes())
 with Image.open(T/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
models=[]
positions=[(1,recovered['state']['continuation']['observation'])]+[(row['turn'],row['source']) for row in read(R/'replans.json')]+[(read(R/'result.json')['model_calls'],calls[-1]['result']['state']['continuation']['observation'])]
for n,o in positions:
 d=R/f'model-{n}';plan=read(d/'plan.json');process=read(d/'process.json');assert process['exit_code']==0
 assert plan['image_sha256']==sha(T/Path(o['image']).name) and plan['runner_sha256']==sha(H/'model_context_runner_v1.py') and plan['instructions_sha256']==sha(H/'screenshot_responder_v1.txt')
 assert (d/'prompt.txt').read_text(encoding='utf-8')==(R/f'prompt-{n}.txt').read_text(encoding='utf-8')
 assert json.loads((d/'prompt.txt').read_text(encoding='utf-8').split('Evidence: ')[1])==(recovered['recovery'] if n==1 else read(R/f'evidence-{n}.json'))
 raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arr=[json.loads(l) for l in (d/'arrivals.jsonl').read_bytes().splitlines()];assert len(raw)==len(arr)==4
 for i,(line,a) in enumerate(zip(raw,arr)):assert a['line']==i and a['sha256']==hashlib.sha256(line).hexdigest() and a['bytes']==len(line)
 e=[json.loads(l) for l in raw];assert [v['type'] for v in e]==['thread.started','turn.started','item.completed','turn.completed'] and e[2]['item']['type']=='agent_message'
 assert json.loads(e[2]['item']['text'])==read(R/f'proposal-{n}.json')
 models.append({'turn':n,'usage':e[3]['usage'],'runner_s':(process['exited_ns']-process['started_ns'])/1e9})
v=read(R/'proposal-1.json');refused=read(R/'target-verdict.json')
from calc_proposal_schema_v1 import validate
assert validate(v)['kind']=='act' and refused['proposal']==v and refused['proposal_submitted'] is False
assert refused['source']==recovered['state']['continuation']['observation']
assert refused['fresh']==calls[7]['result']['state']['continuation']['observation']
assert refused['fresh']['pointer_binding']==refused['source']['pointer_binding']
assert calls[7]['result']['request']['command']['steps']==[{'op':'observe'}]
assert read(R/'result.json')['final_goal_achieved'] is True
rect=ET.parse(T/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');values={k:float(rect.get(k)) for k in ['x','y','width','height']};assert values=={'x':104,'y':50,'width':40,'height':30} and rect.get('transform') is None
assert next(e for e in events if e['event']=='independent_evaluation')['success'] is True
assert read(R/'result.json')['exit_code']==0 and not (R/'error.json').exists() and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
assert all(x['poll'] is None for x in read(R/'live.json'))
from sampled_target_contract_v1 import evaluate
contract=read(R/'contract.json')
with Image.open(T/Path(refused['source']['image']).name) as old,Image.open(T/Path(refused['fresh']['image']).name) as new:
 verdict=evaluate(contract,{'intent':contract['name'],'execute_once':True},refused['source'],refused['fresh'],old,new,refused['clock']['runtime_ns'])
assert verdict==refused['verdict'] and verdict['reason']=='target_patch_changed' and verdict['eligible'] is False
assert read(R/'target-fault.json')==calls[5]['result']
assert calls[5]['result']['request']['command']['steps']==[{'op':'key','key':'Escape'},{'op':'key','key':'Escape'},{'op':'observe'}]
for row in read(R/'replans.json'):
 assert read(R/f"proposal-{row['turn']}.json")==row['proposal']
 subset=calls[row['calls_begin']:row['calls_end']]
 assert subset[1]['result']['request']['command']['steps']==[{'op':'observe'}]
 with Image.open(T/Path(row['source']['image']).name) as old,Image.open(T/Path(row['fresh']['image']).name) as new:
  checked=evaluate(row['contract'],{'intent':row['contract']['name'],'execute_once':True},row['source'],row['fresh'],old,new,row['clock']['runtime_ns'])
 assert checked==row['verdict']
 if row['submitted']:
  assert checked['eligible']
  activation=row['activation'];command=activation['request']['command']
  assert subset[3]['result']==activation
  assert command['steps']==[row['proposal']['steps'][0],{'op':'observe'}]
  assert command['expected_sequence']==checked['expected_sequence'] and command['valid_until_ns']==checked['valid_until_ns']
  assert activation['state']['last_resolution']['terminal']['status']=='completed'
  if 'handoff' in row:
   from activation_handoff_v1 import evaluate as handoff
   gate=row['handoff'];assert len(subset)==8
   assert subset[5]['result']['request']['command']['steps']==[{'op':'observe'}]
   assert gate['fresh']==subset[5]['result']['state']['continuation']['observation']
   assert gate['clock']==subset[6]['result']['state']['last_resolution']['clock']
   assert gate['source']==row['fresh']
   assert handoff(command['id'],command['steps'],activation['state']['last_resolution']['terminal'],gate['source'],gate['fresh'],gate['clock'])==gate['verdict']
   assert gate['verdict']['eligible']
   tail=row['result']['request']['command'];assert subset[7]['result']==row['result']
   assert tail['id']!=command['id']
   assert tail['steps']==row['proposal']['steps'][1:]+[{'op':'observe'}]
   assert all(t['op'] in ('key','chord','text','observe') for t in tail['steps'])
   assert tail['expected_sequence']==gate['fresh']['sequence']
   assert tail['valid_until_ns']==gate['clock']['runtime_ns']+2_000_000_000
  else:assert len(subset)==4 and row['result']==activation
  assert row['result']['state']['last_resolution']['terminal']['status']=='completed'
 else:assert not checked['eligible'] and len(subset)==3
assert read(R/'visual-verdict.json')['kind']=='verify'
assert [read(R/'visual-verdict.json')[k] for k in ['visible_x','visible_y','visible_width','visible_height']]==[104,50,40,30]
from passive_pair_v1 import collect
for row in read(R/'replans.json'):
 if 'readiness' not in row:continue
 ready=row['readiness'];checks=ready['result']['checks'];observations=[]
 subset=calls[ready['calls_begin']:ready['calls_end']];assert len(subset)==3*len(checks)
 for i,check in enumerate(checks):
  triple=subset[3*i:3*i+3]
  assert [x['result']['request']['command']['op'] for x in triple]==['clock','submit','clock']
  assert triple[1]['result']['request']['command']['steps']==[{'op':'observe'}]
  assert check['fresh']==triple[1]['result']['state']['continuation']['observation']
  assert check['clock']==triple[2]['result']['state']['last_resolution']['clock']
  observations.append({'observation':check['fresh'],'image':str(T/Path(check['fresh']['image']).name),'clock':check['clock']})
 o=row['result']['state']['continuation']['observation'];it=iter(observations)
 assert collect({'observation':o,'image':str(T/Path(o['image']).name)},lambda:next(it),ready['contract'],3)==ready['result']
 assert ready['result']['stable']
assert all(t['status']=='completed' for t in terms)
assert all(e['admitted_ns']<e['valid_until_ns'] for e in events if e['event'] in ('input_admission','pointer_admission'))
assert len([r for r in read(R/'replans.json') if 'handoff' in r])==1
report={'episode_classification':'both activation and keyboard phases completed; saved artifact independently verified',
 'events':len(events),'frames':len(obs),'journal_records':count,'exchanges':len(calls),
 'model_calls':models,'svg':values,'svg_sha256':sha(T/'shape.svg'),
 'handoff_elapsed_s':[r['handoff']['elapsed_s'] for r in read(R/'replans.json') if 'handoff' in r],
 'scope':'one live episode with scripted initial edit and fault; later model selection/edit/verification; no general speed claim'}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
