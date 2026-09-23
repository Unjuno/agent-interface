"""Replay live model-selected reconciliation and independent artifact evidence."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start,advance
from append_checkpoint_v1 import load,inspect
from durable_submit_v4 import reconcile
from recovery_view_v1 import present
H=Path(__file__).resolve().parent;R=H/'results/recovery-continue-ink-01';T=R/'runtime'
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
replay(read(R/'initial.json'));calls=read(R/'calls.json');assert len(calls)==8
for c in calls:replay(c['result'])
pending=read(R/'pending.json');before=read(R/'before-loss.json');lost=read(R/'lost-request.json');recovered=read(R/'recovered.json')
assert pending['continuation']==before['continuation']==calls[2]['result']['state']['continuation']
assert pending['pending']['request']==lost and recovered==calls[3]['result']
assert hashlib.sha256((json.dumps(lost)+'\n').encode()).hexdigest()==read(R/'loss.json')['sha256']
assert read(R/'loss.json')['received_response_bytes']==0 and read(R/'blocked.json')['transport_called'] is False
assert recovered['recovery']==present(recovered)
assert 'command' not in recovered['request'] and recovered['request']['action_id']==lost['command']['id']
p,resolution=reconcile(pending['pending'],recovered['reply']['records']);assert p is None and resolution==recovered['state']['last_resolution']
assert load(R/'journal.jsonl')==calls[-1]['result']['state'];count=inspect(R/'journal.jsonl')[1];assert count==17
replay(read(R/'finish.json'))
commands=[e['command'] for e in events if e['event']=='command'];echo=[c for c in commands if c.get('transport_request_id')==lost['request_id']];assert len(echo)==1
assert echo[0]==dict(lost['command'],transport_request_id=lost['request_id'])
assert len([e for e in events if e['event']=='accepted'])==4
assert sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for c in commands for s in c.get('steps',[]))==2
terms=[e for e in events if e['event']=='terminal'];assert len(terms)==4
assert all(t['status']=='completed' and t['release']['verified'] and t['release']['keys_down']==[] and t['release']['buttons_down']==[] for t in terms)
obs=[e for e in events if e['event']=='observation'];decoder=Decoder('live-control')
for n,e in enumerate(obs,1):
 f=decoder.accept((T/f'{n:03d}.ait').read_bytes())
 with Image.open(T/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
models=[]
for n,o in [(1,recovered['state']['continuation']['observation']),(2,calls[-1]['result']['state']['continuation']['observation'])]:
 d=R/f'model-{n}';plan=read(d/'plan.json');process=read(d/'process.json');assert process['exit_code']==0
 assert plan['image_sha256']==sha(T/Path(o['image']).name) and plan['runner_sha256']==sha(H/'model_context_runner_v1.py') and plan['instructions_sha256']==sha(H/'screenshot_responder_v1.txt')
 assert (d/'prompt.txt').read_text(encoding='utf-8')==(R/f'prompt-{n}.txt').read_text(encoding='utf-8')
 assert json.loads((d/'prompt.txt').read_text(encoding='utf-8').split('Evidence: ')[1])==(recovered['recovery'] if n==1 else read(R/'continued-view.json'))
 raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arr=[json.loads(l) for l in (d/'arrivals.jsonl').read_bytes().splitlines()];assert len(raw)==len(arr)==4
 for i,(line,a) in enumerate(zip(raw,arr)):assert a['line']==i and a['sha256']==hashlib.sha256(line).hexdigest() and a['bytes']==len(line)
 e=[json.loads(l) for l in raw];assert [v['type'] for v in e]==['thread.started','turn.started','item.completed','turn.completed'] and e[2]['item']['type']=='agent_message'
 assert json.loads(e[2]['item']['text'])==read(R/f'proposal-{n}.json')
 models.append({'turn':n,'usage':e[3]['usage'],'runner_s':(process['exited_ns']-process['started_ns'])/1e9})
v=read(R/'proposal-2.json');assert v['kind']=='verify' and [v[k] for k in ['visible_x','visible_y','visible_width','visible_height']]==[104,50,40,30]
rect=ET.parse(T/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');values={k:float(rect.get(k)) for k in ['x','y','width','height']};assert values=={'x':104,'y':50,'width':40,'height':30} and rect.get('transform') is None
assert next(e for e in events if e['event']=='independent_evaluation')['success'] is True
assert read(R/'result.json')['exit_code']==0 and not (R/'error.json').exists() and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
assert all(x['poll'] is None for x in read(R/'live.json'))
continued=read(R/'continued.json');proposal=read(R/'proposal-1.json')
from calc_proposal_schema_v1 import validate
assert validate(proposal)['kind']=='act'
assert continued['proposal']==proposal and continued['result']==calls[-1]['result']
assert calls[-1]['result']['request']['command']['steps']==proposal['steps']+[{'op':'observe'}]
assert continued['fresh']['sequence']>continued['source']['sequence'] and continued['fresh']['pointer_binding']==continued['source']['pointer_binding']
for cc,ac in [(calls[4],calls[5]),(calls[6],calls[7])]:
 clock=cc['result']['state']['last_resolution']['clock'];command=ac['result']['request']['command']
 assert command['expected_sequence']==clock['sequence'] and command['valid_until_ns']==clock['runtime_ns']+30_000_000_000
assert calls[5]['result']['request']['command']['steps']==[{'op':'observe'}]
assert read(R/'continued-view.json')==present(calls[-1]['result'])
assert calls[-1]['result']['request']['command']['id']!=lost['command']['id']
report={'events':len(events),'frames':len(obs),'journal_records':count,'model_calls':models,'svg':values,'svg_sha256':sha(T/'shape.svg'),'scope':'one live intentional response abandonment; scripted edit, caller recovery read, new model edit and verification; not full autonomous editing or general recovery', 'loss_to_read_resolution_s':(calls[3]['end_ns']-read(R/'loss.json')['send_completed_ns'])/1e9}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
