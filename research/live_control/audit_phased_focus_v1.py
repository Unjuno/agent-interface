"""Audit real inter-phase focus refusal and unchanged saved artifact."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start,advance
from append_checkpoint_v1 import load,inspect
from activation_handoff_v1 import evaluate
from sampled_target_contract_v1 import evaluate as target
H=Path(__file__).resolve().parent;R=H/'results/phased-focus-01';T=R/'runtime'
sys.path.insert(0,str(H.parent/'observation_tiles'))
from tile_transport import Decoder
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n,s in read(R/'plan.json')['sources'].items():assert sha(H/n)==s
for n,s in read(T/'sources.json').items():assert sha(H.parent/n)==s
events=[json.loads(l) for l in (T/'events.jsonl').read_bytes().splitlines()]
ep=read(R/'endpoint.json');state=start(ep['socket'])
def replay(r):
 global state
 q,a=r['request'],r['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
 state=advance(state,ep['socket'],q['after'],a)
 assert state==r.get('state',{}).get('continuation',r.get('continuation'))
replay(read(R/'initial.json'));calls=read(R/'calls.json')
for c in calls:replay(c)
assert load(R/'journal.jsonl')==calls[-1]['state']
assert inspect(R/'journal.jsonl')[1]==1+2*len(calls)
replay(read(R/'finish.json'))
data=read(R/'input.json');phases=read(R/'phases.json');subset=calls[data['calls_begin']:]
assert len(subset)==4 and subset==phases['exchanges']
assert phases['reason']=='handoff_refused' and phases['tail_submitted'] is False
activation=subset[0];cmd=activation['request']['command'];terminal=activation['state']['last_resolution']['terminal']
assert terminal['status']=='completed' and terminal['steps_completed']==2
assert cmd['steps']==[data['proposal']['steps'][0],{'op':'observe'}]
assert cmd['expected_sequence']==data['checked']['expected_sequence'] and cmd['valid_until_ns']==data['checked']['valid_until_ns']
assert subset[1]['request']['command']['op']=='clock'
assert subset[2]['request']['command']['steps']==[{'op':'observe'}]
gate=phases['handoff'];assert gate['source']==data['source']
assert gate['fresh']==subset[2]['state']['continuation']['observation']
assert gate['clock']==subset[3]['state']['last_resolution']['clock']
assert evaluate(cmd['id'],cmd['steps'],terminal,gate['source'],gate['fresh'],gate['clock'])==gate['verdict']
assert gate['verdict']['reason']=='binding_changed_or_missing'
fault=read(R/'fault.json');assert fault['activation_id']==cmd['id']
assert fault['focus_after']==fault['sink']==gate['fresh']['input_focus_before']==gate['fresh']['input_focus_after']
assert gate['fresh']['capture_ns']>terminal['terminal_ns']
ready=read(R/'readiness.json')
for check in ready['checks']:
 with Image.open(T/Path(check['source']['image']).name) as old,Image.open(T/Path(check['fresh']['image']).name) as new:
  assert target(data['contract'],{'intent':data['contract']['name'],'execute_once':True},check['source'],check['fresh'],old,new,check['clock']['runtime_ns'])==check['verdict']
assert ready['checks'][-1]['verdict']==data['checked']
commands=[e['command'] for e in events if e['event']=='command']
assert all(s['op'] in ('pointer_click','observe') for c in commands for s in c.get('steps',[]))
assert sum(s['op']=='pointer_click' for c in commands for s in c.get('steps',[]))==2
terms=[e for e in events if e['event']=='terminal']
assert len(terms)==len([e for e in events if e['event']=='accepted'])
assert all(t['status']=='completed' and t['release']['verified'] and t['release']['keys_down']==[] and t['release']['buttons_down']==[] for t in terms)
assert all(e['admitted_ns']<e['valid_until_ns'] for e in events if e['event'] in ('input_admission','pointer_admission'))
decoder=Decoder('live-control');obs=[e for e in events if e['event']=='observation']
for i,e in enumerate(obs,1):
 f=decoder.accept((T/f'{i:03d}.ait').read_bytes())
 with Image.open(T/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
rect=ET.parse(T/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');values={k:float(rect.get(k)) for k in ['x','y','width','height']}
assert values=={'x':50,'y':50,'width':40,'height':30} and rect.get('transform') is None
assert read(R/'result.json')=={'exit_code':0,'expected_refusal':True,'final_goal_achieved':False,'model_calls':0}
assert not (R/'error.json').exists() and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
report={'scope':'real scripted inter-phase X11 focus fault; no model or edit success','events':len(events),'frames':len(obs),'exchanges':len(calls),'phase_exchanges':len(subset),'reason':gate['verdict']['reason'],'keyboard_tail_sent':False,'saved_svg':values,'handoff_s':gate['elapsed_s']}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
