"""Audit actual observation/model/revalidation chain without mixing clock domains."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/live-focus-boundary-01';run=r/'runtime';model=r/'model'
 for n,h in read(r/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(run/'manifest.json')['sources'].items():assert sha(HERE.parent/n)==h,n
 mp=read(model/'plan.json');assert sha(model/'prompt.txt')==sha(r/'prompt.txt')==mp['stdin_sha256']==read(r/'prepared.json')['prompt_sha256']
 assert sha(HERE.parent/'live_control/model_text_runner_v1.py')==mp['runner_sha256']
 raw=(model/'events.jsonl').read_bytes().splitlines(keepends=True);arr=[json.loads(l) for l in (model/'arrivals.jsonl').read_text().splitlines()]
 for n,(line,a) in enumerate(zip(raw,arr)):assert a['line']==n and a['sha256']==hashlib.sha256(line).hexdigest()
 assert len(raw)==len(arr)
 me=[json.loads(l) for l in raw];items=[e['item'] for e in me if e['type']=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message'
 answer=json.loads(items[0]['text']);decision=read(r/'decision.json');assert answer==decision['model_answer'] and answer['proposal']=='propose_new_target_action'
 assert read(model/'process.json')['exit_code']==0
 events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()];state=read(r/'state.json');cursor=0
 for call in state['calls']:
  q,a=call['request'],call['reply'];assert q['after']==cursor and a['records']==events[cursor:a['cursor']];cursor=a['cursor']
 assert cursor==len(events)
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==3
 capture=obs[1]['capture_ns'];assert capture==decision['source_capture_ns']
 assert decision['revalidated_age_ms']==(decision['revalidation_clock_ns']-capture)/1e6>1000
 assert read(r/'prepared.json')['age_ms']<1000
 assert decision['dispatch']=='observe_only'
 commands=[e['command'] for e in events if e['event']=='command'];submits=[c for c in commands if c['op']=='submit']
 assert [c['id'] for c in submits]==['model-observation','stale-reobservation'] and all(c['steps']==[{'op':'observe'}] for c in submits)
 assert not any(e['event'] in ('input_admission','pointer_admission') for e in events)
 admitted=next(e for e in events if e['event']=='accepted' and e['id']=='stale-reobservation')
 assert admitted['accepted_ns']>decision['revalidation_clock_ns']
 dec=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=dec.accept((run/f'{n:03d}.ait').read_bytes())
  with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 assert read(run/'evaluation.json')['contract_satisfied'] is False
 assert read(run/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True}
 process=read(model/'process.json');usage=next(e['usage'] for e in me if e['type']=='turn.completed')
 report={'events':len(events),'calls':len(state['calls']),'frames':len(obs),'prompt_preparation_age_ms':read(r/'prepared.json')['age_ms'],'post_model_age_ms':decision['revalidated_age_ms'],'source_capture_to_reobserve_accept_ms':(admitted['accepted_ns']-capture)/1e6,'source_capture_to_new_image_ready_ms':(obs[-1]['image_ready_ns']-capture)/1e6,'local_model_runner_ms':(process['exited_ns']-process['started_ns'])/1e6,'usage':usage,'clock_scope':'age and capture-to-reobserve use runtime clock; runner duration separate Windows clock; no cross-clock subtraction','scope':'one guided text-only live proposal, stale veto and observe-only followup; no target action or autonomous gameplay','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
