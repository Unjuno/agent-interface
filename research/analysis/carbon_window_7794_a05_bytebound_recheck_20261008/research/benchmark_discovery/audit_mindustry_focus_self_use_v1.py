"""Audit assistant-driven AltTab recovery across intentional focus change."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
from mindustry_bend_build_score_v1 import score
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/mindustry-focus-self-use-01';run=r/'runtime'
 for p,h in read(run/'manifest.json')['sources'].items():assert sha(HERE.parent/p)==h,p
 events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()]
 stages=['initial','clock-initial','fault','fault-terminal','clock-refocus','refocus','clock-verify','verify-pointer','finish'];cursor=0
 for stage in stages:
  q,a=read(r/stage/'request.json'),read(r/stage/'reply.json');assert q['after']==cursor and a['records']==events[cursor:a['cursor']];cursor=a['cursor']
 assert cursor==len(events)
 submitted=[e['command'] for e in events if e['event']=='command' and e['command']['op']=='submit']
 assert [c['id'] for c in submitted]==['fault','refocus','verify-pointer']
 assert submitted[1]['steps']==[{'op':'chord','modifier':'Alt_L','key':'Tab'},{'op':'observe'}]
 terminals=[e for e in events if e['event']=='terminal'];assert [e['status'] for e in terminals]==['needs_decision','needs_decision','completed']
 assert all(e['release']['verified'] is True for e in terminals)
 assert not any(e['event']=='step_started' and e.get('id') in ('fault','refocus') and e['step']==1 for e in events)
 assert not any(e['event']=='fixture_focus_restored' for e in events)
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==9
 assert obs[1]['pointer_binding'] is None
 assert obs[5]['pointer_binding']==obs[0]['pointer_binding']==obs[-1]['pointer_binding']
 assert submitted[2]['expected_sequence']==6
 dec=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=dec.accept((run/f'{n:03d}.ait').read_bytes())
  with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 finish=next(e for e in events if e['event']=='command' and e['command']['op']=='finish');assert 'gui_judgment' in finish['command']
 actual=score(*[read(run/n) for n in ('before.json','delivery-before.json','after.json')],read(HERE/'mindustry_bend_plan_v1.json'))
 assert actual==read(run/'evaluation.json') and actual['contract_satisfied'] is False and actual['copper_delta']==0
 assert read(run/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True}
 report={'events':len(events),'exchanges':len(stages),'exact_frames':len(obs),'viewed_image_sequences':[1,2,5,9],'fault_terminal_to_refocus_terminal_ms':(terminals[1]['terminal_ns']-terminals[0]['terminal_ns'])/1e6,'fault_terminal_to_pointer_verify_terminal_ms':(terminals[2]['terminal_ns']-terminals[0]['terminal_ns'])/1e6,'scope':'known manual self-use; focus restored by AltTab before fixture cleanup; no model receipt/cost measurement','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
