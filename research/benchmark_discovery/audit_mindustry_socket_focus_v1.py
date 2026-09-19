"""Audit same-action stopped/terminal socket recovery against actual GUI events."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'));sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from stopped_client_v1 import PendingAction
from tile_transport import Decoder
from mindustry_bend_build_score_v1 import score
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/mindustry-socket-focus-02';run=r/'runtime'
 for n,h in read(r/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(run/'manifest.json')['sources'].items():assert sha(HERE.parent/n)==h,n
 events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()];calls=read(r/'calls.json');cursor=0;tracker=None;seen=[]
 for call in calls:
  q,a=call['request'],call['reply'];assert q['after']==cursor
  if q.get('command',{}).get('id')=='focus-drag':tracker=PendingAction('focus-drag',cursor)
  if tracker is not None and tracker.terminal is None:seen.append(tracker.ingest(cursor,a))
  assert a['records']==events[cursor:a['cursor']];cursor=a['cursor']
 assert tracker.uncertainty is None and tracker.stopped and tracker.terminal
 assert any(s['state']=='input_stopped_capture_pending' for s in seen)
 assert tracker.terminal['status']=='needs_decision' and tracker.terminal['decision_reason']=='focus_changed'
 assert sum(c['request'].get('command',{}).get('op')=='finish' for c in calls)==1
 assert sum(c['request'].get('command',{}).get('id')=='focus-drag' for c in calls)==1
 assert [e['operation'] for e in events if e['event']=='pointer_admission']==['move','button_down']
 assert not any(e['event']=='step_started' and e.get('id')=='focus-drag' and e['step']!=0 for e in events)
 assert next(e for e in events if e['event']=='fixture_focus_transferred')['physical_button_down'] is True
 stop=next(e for e in events if e['event']=='input_stopped');assert stop['release']['verified']
 observations=[e for e in events if e['event']=='observation'];assert len(observations)==4
 assert len([e for e in observations if e['id']=='focus-drag'])==2
 decoder=Decoder('live-control')
 for n,e in enumerate(observations,1):
  f=decoder.accept((run/f'{n:03d}.ait').read_bytes())
  with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 assert events.index(next(e for e in events if e['event']=='fixture_focus_restored'))>events.index(observations[-1])
 actual=score(*[read(run/n) for n in ('before.json','delivery-before.json','after.json')],read(HERE/'mindustry_bend_plan_v1.json'))
 assert actual==read(run/'evaluation.json') and actual['contract_satisfied'] is False
 assert read(run/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True}
 assert read(r/'result.json')['exit_code']==0
 report={'events':len(events),'socket_calls':len(calls),'exact_frames':len(observations),'same_action_pending_then_terminal':True,'finish_forwarded_once':True,'scope':'scripted GUI focus interruption; fixture restores focus after recovery; no model boundary or agent gameplay claim','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
