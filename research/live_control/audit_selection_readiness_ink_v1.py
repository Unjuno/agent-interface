"""Replay live model-selected reconciliation and independent artifact evidence."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start,advance
from append_checkpoint_v1 import load,inspect
from durable_submit_v4 import reconcile
H=Path(__file__).resolve().parent;R=H/'results/selection-readiness-ink-01';T=R/'runtime'
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
replay(read(R/'initial.json'));calls=read(R/'calls.json');assert len(calls)==24
for c in calls:replay(c['result'])
pending=read(R/'pending.json');before=read(R/'before-loss.json');lost=read(R/'lost-request.json');recovered=read(R/'recovered.json')
assert pending['continuation']==before['continuation']==calls[2]['result']['state']['continuation']
assert pending['pending']['request']==lost and recovered==calls[3]['result']
assert hashlib.sha256((json.dumps(lost)+'\n').encode()).hexdigest()==read(R/'loss.json')['sha256']
assert read(R/'loss.json')['received_response_bytes']==0 and read(R/'blocked.json')['transport_called'] is False
assert 'command' not in recovered['request'] and recovered['request']['action_id']==lost['command']['id']
p,resolution=reconcile(pending['pending'],recovered['reply']['records']);assert p is None and resolution==recovered['state']['last_resolution']
assert load(R/'journal.jsonl')==calls[-1]['result']['state'];count=inspect(R/'journal.jsonl')[1];assert count==49
replay(read(R/'finish.json'))
commands=[e['command'] for e in events if e['event']=='command'];echo=[c for c in commands if c.get('transport_request_id')==lost['request_id']];assert len(echo)==1
assert echo[0]==dict(lost['command'],transport_request_id=lost['request_id'])
assert len([e for e in events if e['event']=='accepted'])==12
assert sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for c in commands for s in c.get('steps',[]))==1
terms=[e for e in events if e['event']=='terminal'];assert len(terms)==12
assert all(t['status']=='completed' and t['release']['verified'] and t['release']['keys_down']==[] and t['release']['buttons_down']==[] for t in terms)
obs=[e for e in events if e['event']=='observation'];decoder=Decoder('live-control')
for n,e in enumerate(obs,1):
 f=decoder.accept((T/f'{n:03d}.ait').read_bytes())
 with Image.open(T/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
models=[]
rect=ET.parse(T/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');values={k:float(rect.get(k)) for k in ['x','y','width','height']};assert values=={'x':88,'y':50,'width':40,'height':30} and rect.get('transform') is None
assert next(e for e in events if e['event']=='independent_evaluation')['success'] is True
assert read(R/'result.json')['exit_code']==0 and not (R/'error.json').exists() and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
assert all(x['poll'] is None for x in read(R/'live.json'))
samples=read(R/'samples.json');assert len(samples)==9
assert samples[0]['label']=='selected-result' and [x['label'] for x in samples[1:]]==['0','0.1','0.25','0.5','1','2','4','8']
for index,sample in enumerate(samples):
 expected=calls[7 if index==0 else 9+2*(index-1)]['result']['state']['continuation']['observation']
 assert sample['observation']==expected
 with Image.open(T/Path(expected['image']).name) as im:
  patch=im.crop([538,94,563,119]);assert hashlib.sha256(patch.tobytes()).hexdigest()==sample['patch_sha256'] and list(patch.getpixel((12,12)))==sample['center_pixel']
assert all(c['result']['request']['command']['steps']==[{'op':'observe'}] for c in calls[9::2])
assert len({json.dumps(x['observation']['pointer_binding'],sort_keys=True) for x in samples})==1
report={'events':len(events),'frames':len(obs),'journal_records':count,'model_calls':models,'svg':values,'svg_sha256':sha(T/'shape.svg'),'scope':'scripted selection and passive sampling, no model; one readiness trace', 'samples':[{'label':x['label'],'elapsed_s':x['driver_elapsed_s'],'capture_ns':x['observation']['capture_ns'],'hash':x['patch_sha256'],'center':x['center_pixel']} for x in samples], 'loss_to_read_resolution_s':(calls[3]['end_ns']-read(R/'loss.json')['send_completed_ns'])/1e9}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
