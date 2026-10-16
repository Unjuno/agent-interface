"""Audit actual shared-contract click, retained failures and independent SVG effect."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
from sampled_target_contract_v1 import evaluate
from early_exchange_v1 import own_command

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/inkscape-guarded-click-01';run=r/'runtime';events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()]
 for n,h in read(run/'sources.json').items():assert sha(HERE.parent/n)==h,n
 for stage in ('focus-x','focus-x-current','focus-x-reconciled'):
  for n,h in read(r/stage/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
  for c in read(r/stage/'calls.json'):
   q,a=c['request'],c['reply'];assert a['records']==events[q['after']:a['cursor']]
 for stage in ('initial','clock-select','select','clock-edit','edit-save','finish'):
  q,a=read(r/stage/'request.json'),read(r/stage/'reply.json');assert a['records']==events[q['after']:a['cursor']]
 assert read(r/'focus-x/decision.json')['decision']=={'eligible':False,'reason':'target_patch_changed'}
 assert read(r/'patch-difference.json')['different_pixels']==228
 rejected=[e for e in events if e['event']=='rejected'];assert len(rejected)==1 and rejected[0]['reason']=='intent validity expired'
 assert not any(e['event']=='accepted' and e.get('id')=='focus-x-current-observe' for e in events)
 calls=read(r/'focus-x-reconciled/calls.json')
 for c in calls:
  if c['request']['command']['op']=='clock':
   records=c['reply']['records'];i=own_command(records,c['request']['request_id'],'clock');assert len(records[i+1:])==1 and records[-1]['event']=='clock'
 plan=read(r/'focus-x-reconciled/plan.json');d=read(r/'focus-x-reconciled/decision.json');source=plan['source_observation'];fresh=d['fresh_observation']
 with Image.open(run/Path(source['image']).name) as old,Image.open(run/Path(fresh['image']).name) as new:
  assert evaluate(plan['spec']['contract'],plan['spec']['intent'],source,fresh,old,new,d['clock']['runtime_ns'])==d['decision']
 assert d['decision']['eligible'] and fresh['sequence']==5
 inputs=[e for e in events if e['event']=='pointer_admission' and e.get('id')=='focus-x-reconciled'];assert [e['operation'] for e in inputs]==['move','button_down']
 assert all(e['input_ack_ns']<d['decision']['valid_until_ns'] for e in inputs)
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==12;dec=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=dec.accept((run/f'{n:03d}.ait').read_bytes())
  with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 terms=[e for e in events if e['event']=='terminal'];assert len(terms)==5 and all(e['status']=='completed' and e['release']['verified'] for e in terms)
 finish=next(e for e in events if e['event']=='command' and e['command']['op']=='finish');assert 'gui_judgment' in finish['command']
 rect=ET.parse(run/'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect');values={k:float(rect.get(k)) for k in ('x','y','width','height')}
 assert values=={'x':92.,'y':50.,'width':40.,'height':30.} and rect.get('transform') is None
 result={'events':len(events),'exact_frames':len(obs),'accepted_programs':len(terms),'rejected_programs':1,'saved_svg':values,'svg_sha256':sha(run/'shape.svg'),'fresh_capture_to_guarded_button_ack_ms':(inputs[-1]['input_ack_ns']-fresh['capture_ns'])/1e6,'initial_capture_to_final_input_terminal_ms':(terms[-1]['terminal_ns']-obs[0]['capture_ns'])/1e6,'scope':'actual assistant desktop self-use, independent saved effect; guard covers focus click only, keyboard/save separately admitted','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
