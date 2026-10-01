"""Audit actual changed-target/focus refusal and strict proposal type controls."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
from menu_intent_guard_v1 import check as old_check
from menu_intent_guard_v2 import check

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rows=[]
 for name,kind,reason in [('live-menu-mutation-patch-02','patch','target_patch_changed'),('live-menu-mutation-focus-01','focus','binding_changed')]:
  r=HERE/'results'/name;run=r/'runtime';d=read(r/'decision.json');state=read(r/'state.json')
  for n,h in read(r/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
  for n,h in read(run/'manifest.json')['sources'].items():assert sha(HERE.parent/n)==h,n
  mp=read(r/'model/plan.json');assert sha(r/'prompt.txt')==sha(r/'model/prompt.txt')==mp['stdin_sha256']
  assert sha(HERE.parent/'live_control/model_text_runner_v1.py')==mp['runner_sha256']
  me=[json.loads(l) for l in (r/'model/events.jsonl').read_text().splitlines()];items=[e['item'] for e in me if e['type']=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message'
  assert json.loads(items[0]['text'])==d['model_answer'] and read(r/'model/process.json')['exit_code']==0
  events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()];cursor=0
  for call in state['calls']:
   q,a=call['request'],call['reply'];assert q['after']==cursor and a['records']==events[cursor:a['cursor']];cursor=a['cursor']
  assert cursor==len(events)
  mutation=next(e for e in events if e['event']=='fixture_mutation');restored=next(e for e in events if e['event']=='fixture_restored')
  assert mutation['kind']==kind and state['prepared_clock']['runtime_ns']<mutation['at_ns']<d['fresh_observation']['capture_ns']<restored['at_ns']
  assert not any(e['event'] in ('pointer_admission','input_admission') for e in events)
  assert [e['id'] for e in events if e['event']=='accepted']==['model-observation','intent-revalidation']
  obs=[e for e in events if e['event']=='observation'];assert len(obs)==3;dec=Decoder('live-control')
  for n,e in enumerate(obs,1):
   f=dec.accept((run/f'{n:03d}.ait').read_bytes())
   with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
  with Image.open(run/Path(state['source_observation']['image']).name) as old,Image.open(run/Path(d['fresh_observation']['image']).name) as new:
   assert check(d['model_answer'],state['source_observation'],d['fresh_observation'],old,new,d['revalidation_clock_ns'])==d['guard']=={'eligible':False,'reason':reason}
  assert read(run/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True} and read(run/'evaluation.json')['contract_satisfied'] is False
  rows.append({'case':kind,'refusal':reason,'events':len(events),'calls':len(state['calls']),'model_usage':next(e['usage'] for e in me if e['type']=='turn.completed'),'zero_input_admissions':True})
 r=HERE/'results/live-menu-intent-01';d=read(r/'decision.json');s=read(r/'state.json')['source_observation'];controls={}
 with Image.open(r/'runtime'/Path(s['image']).name) as old,Image.open(r/'runtime'/Path(d['fresh_observation']['image']).name) as new:
  args=(s,d['fresh_observation'],old,new,d['revalidation_clock_ns'])
  assert check(d['model_answer'],*args)==d['guard']
  numeric={'intent':'select_basic_conveyor','execute_once':1};assert old_check(numeric,*args)['eligible'] is True
  for name,bad in [('numeric_bool',numeric),('extra_field',{**d['model_answer'],'repeat':2}),('array',[])]:
   result=check(bad,*args);assert result=={'eligible':False,'reason':'invalid_intent_schema'};controls[name]=result
  assert check(d['model_answer'],s,{},old,new,0)=={'eligible':False,'reason':'invalid_observation_metadata'}
 report={'cases':rows,'strict_type_controls':controls,'positive_archived_guard_unchanged':True,'audit_sha256':sha(Path(__file__)),'scope':'two live fixture mutations between prompt preparation and revalidation; model-internal timing unknown; fixture restores after capture'}
 (HERE/'results/live-menu-mutation-focus-01/audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
