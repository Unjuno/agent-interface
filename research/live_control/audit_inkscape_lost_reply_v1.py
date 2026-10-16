"""Audit real lost-reply continuation, one input program and saved SVG effect."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start,advance
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/inkscape-lost-reply-01';run=r/'runtime';plan=read(r/'plan.json')
 for n,h in plan['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(run/'sources.json').items():assert sha(HERE.parent/n)==h,n
 events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()];calls=read(r/'calls.json');ep=read(r/'endpoint.json');state=start(ep['socket'])
 for c in calls:
  q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
  state=advance(state,ep['socket'],q['after'],a);assert state==c['continuation']
 assert state==read(r/'continuation.json')
 loss=read(r/'loss.json');lost=read(r/'lost-request.json')
 assert hashlib.sha256((json.dumps(lost)+'\n').encode()).hexdigest()==loss['request_sha256']
 assert loss['received_response_bytes']==0 and loss['automatic_resend'] is False
 assert read(r/'before-loss.json')==calls[3]['continuation']
 recovered=read(r/'recovered.json');assert 'command' not in recovered['request']
 assert recovered['request']['after']==read(r/'before-loss.json')['cursor']
 requests=[c['request'] for c in calls]+[lost]
 assert sum(q.get('command',{}).get('id')=='move-save' for q in requests)==1
 assert [e['id'] for e in events if e['event']=='accepted']==['select','move-save']
 echoes=[e for e in events if e['event']=='command' and e['command'].get('transport_request_id')=='move-save-once'];assert len(echoes)==1
 steps=echoes[0]['command']['steps'];assert sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for s in steps)==1
 terms=[e for e in events if e['event']=='terminal'];assert len(terms)==2 and all(t['status']=='completed' and t['release']['verified'] for t in terms)
 assert not any(e['event']=='rejected' for e in events)
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==9;dec=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=dec.accept((run/f'{n:03d}.ait').read_bytes())
  with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 rect=ET.parse(run/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');values={k:float(rect.get(k)) for k in ('x','y','width','height')};assert values==plan['expected_svg'] and rect.get('transform') is None
 assert read(r/'result.json')['exit_code']==0 and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
 report={'events':len(events),'received_replies':len(calls),'abandoned_response_requests':1,'move_save_submissions':1,'save_chord_steps':1,'frames':len(obs),'svg':values,'svg_sha256':sha(run/'shape.svg'),'recovered_image_sequence':state['observation']['sequence'],'scope':'scripted actual GUI and deliberate close after sendall; no natural outage or model latency claim','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
