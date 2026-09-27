"""Audit actual Mindustry cancellation/re-observation evidence."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
from mindustry_bend_build_score_v1 import score
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/mindustry-runtime-cancel-01';d=HERE/'results/mindustry-runtime-cancel-driver-01'
 for p,h in read(r/'manifest.json')['sources'].items():assert sha(HERE.parent/p)==h,p
 assert sha(HERE/'probe_mindustry_runtime_cancel_v1.py')==read(d/'plan.json')['driver_sha256']
 e=[json.loads(l) for l in (r/'events.jsonl').read_text().splitlines()]
 assert e==[json.loads(l) for l in (d/'stdout.jsonl').read_text().splitlines()]
 submitted=[x['command'] for x in e if x['event']=='command' and x['command']['op']=='submit']
 assert [x['id'] for x in submitted]==['cancel-drag','observe-recovery']
 assert submitted[1]['steps']==[{'op':'observe'}]
 admissions=[x for x in e if x['event']=='pointer_admission'];assert [x['operation'] for x in admissions]==['move','button_down']
 cancel=next(x for x in e if x['event']=='cancel_requested');assert cancel['matched'] is True
 t=[x for x in e if x['event']=='terminal'];assert [x['status'] for x in t]==['cancelled','completed']
 assert t[0]['steps_completed']==0 and all(x['release']['verified'] for x in t)
 assert not any(x['event']=='step_started' and x.get('id')=='cancel-drag' and x['step']!=0 for x in e)
 cause=t[0]['interruption']['record'];assert cause in read(r/'owner-events.json') and cause['reason']=='cancelled'
 assert admissions[-1]['input_ack_ns']<cancel['requested_ns']<=cause['verified_ns']<=t[0]['terminal_ns']
 dec=Decoder('live-control');observations=[x for x in e if x['event']=='observation']
 for n,x in enumerate(observations,1):
  assert x['sequence']==n
  frame=dec.accept((r/f'{n:03d}.ait').read_bytes())
  with Image.open(r/Path(x['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(frame.width,frame.height,frame.mode,frame.pixels)
 assert len(observations)==2
 for k in ('input_state_before','input_state_after'):
  assert observations[-1][k]['owned_buttons']==[] and observations[-1][k]['owned_keycodes']==[]
 a=score(*[read(r/n) for n in ('before.json','delivery-before.json','after.json')],read(HERE/'mindustry_bend_plan_v1.json'))
 assert a==read(r/'evaluation.json') and a['contract_satisfied'] is False and a['copper_delta']==0
 assert read(r/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True}
 assert read(d/'result.json')['exit_code']==0
 result={'scope':'single scripted live GUI cancel; no focus-loss, socket or gameplay success proof','events':len(e),'exact_frames':len(observations),'cancel_to_verified_release_ms':(cause['verified_ns']-cancel['requested_ns'])/1e6,'cancel_to_terminal_ms':(t[0]['terminal_ns']-cancel['requested_ns'])/1e6,'recovery_accept_to_image_ready_ms':(observations[-1]['image_ready_ns']-next(x['accepted_ns'] for x in e if x['event']=='accepted' and x['id']=='observe-recovery'))/1e6,'audit_sha256':sha(Path(__file__))}
 (d/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
