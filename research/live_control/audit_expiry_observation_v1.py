"""Audit real expiry preserves status, stops input and returns post-release samples."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start,advance
H=Path(__file__).resolve().parent;R=H/'results/expiry-observation-01';T=R/'runtime'
sys.path.insert(0,str(H.parent/'observation_tiles'))
from tile_transport import Decoder
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n,d in read(R/'plan.json')['sources'].items():assert sha(H/n)==d
for n,d in read(T/'sources.json').items():assert sha(H.parent/n)==d
events=[json.loads(l) for l in (T/'events.jsonl').read_bytes().splitlines()];calls=read(R/'calls.json');ep=read(R/'endpoint.json');state=start(ep['socket'])
assert len(calls)==4
for c in calls:
 q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
 state=advance(state,ep['socket'],q['after'],a);assert state==c['continuation']
terms=[e for e in events if e['event']=='terminal'];assert len(terms)==1;t=terms[0]
assert t['status']=='expired' and t['steps_completed']==0 and t['release']['verified'] and t['release']['keys_down']==[] and t['release']['buttons_down']==[]
assert not any(e['event']=='step_started' and e['step']==1 for e in events)
assert [e['key'] for e in events if e['event']=='input_admission']==['Shift_L']
assert any(e['event']=='keys_held' for e in events)
assert all(e['admitted_ns']<e['valid_until_ns'] for e in events if e['event'] in ('input_admission','pointer_admission'))
stop=next(e for e in events if e['event']=='input_stopped');assert stop['decision_reason']=='expired' and stop['release']['verified']
post=t['post_release_observation'];assert post['captures']==2 and not post['stopped'] and post['error'] is None
samples=[e for e in events if e['event']=='observation' and e['sequence'] in post['sequences']];assert len(samples)==2
assert all(t['release']['verified_ns']<e['capture_ns']<t['terminal_ns'] for e in samples)
assert calls[2]['continuation']['observation']==samples[-1]
assert not any(e['event'] in ('step_started','input_admission','pointer_admission') for e in events[events.index(stop)+1:events.index(t)])
obs=[e for e in events if e['event']=='observation'];decoder=Decoder('live-control')
for n,e in enumerate(obs,1):
 frame=decoder.accept((T/f'{n:03d}.ait').read_bytes())
 with Image.open(T/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(frame.width,frame.height,frame.mode,frame.pixels)
rect=ET.parse(T/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');actual={k:float(rect.get(k)) for k in ['x','y','width','height']};assert actual=={'x':50,'y':50,'width':40,'height':30}
assert read(R/'result.json')['exit_code']==0 and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
report={'events':len(events),'exact_frames':len(obs),'status':t['status'],'post_release_captures':2,'release_to_latest_capture_ms':(samples[-1]['capture_ns']-t['release']['verified_ns'])/1e6,'release_to_terminal_ms':(t['terminal_ns']-t['release']['verified_ns'])/1e6,'saved_svg':actual,'scope':'real expired modifier hold, no trailing text or lease renewal; not editing success'}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
