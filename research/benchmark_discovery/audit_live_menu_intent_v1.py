"""Audit one model proposal followed by fresh target validation and one click."""
import copy,hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
from menu_intent_guard_v1 import check
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/live-menu-intent-01';run=r/'runtime';model=r/'model'
 for n,h in read(r/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(run/'manifest.json')['sources'].items():assert sha(HERE.parent/n)==h,n
 mp=read(model/'plan.json');assert sha(model/'prompt.txt')==sha(r/'prompt.txt')==mp['stdin_sha256'];assert sha(HERE.parent/'live_control/model_text_runner_v1.py')==mp['runner_sha256']
 me=[json.loads(l) for l in (model/'events.jsonl').read_text().splitlines()];items=[e['item'] for e in me if e['type']=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message'
 d=read(r/'decision.json');assert json.loads(items[0]['text'])==d['model_answer']
 assert read(model/'process.json')['exit_code']==0
 events=[json.loads(l) for l in (run/'events.jsonl').read_text().splitlines()];state=read(r/'state.json');cursor=0
 for call in state['calls']:
  q,a=call['request'],call['reply'];assert q['after']==cursor and a['records']==events[cursor:a['cursor']];cursor=a['cursor']
 assert cursor==len(events)
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==5
 dec=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=dec.accept((run/f'{n:03d}.ait').read_bytes())
  with Image.open(run/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 fresh=d['fresh_observation'];source=state['source_observation'];assert fresh['sequence']>source['sequence'] and d['old_observation_age_ms']>1000
 with Image.open(run/Path(source['image']).name) as old,Image.open(run/Path(fresh['image']).name) as new:
  assert check(d['model_answer'],source,fresh,old,new,d['revalidation_clock_ns'])==d['guard'] and d['guard']['eligible']
  controls={}
  for name in ('stale','changed_binding','same_sequence','changed_patch','unsupported_intent'):
   f=copy.deepcopy(fresh);im=new.copy();intent=copy.deepcopy(d['model_answer']);now=d['revalidation_clock_ns']
   if name=='stale':now=f['capture_ns']+1_000_000_000
   elif name=='changed_binding':f['pointer_binding']=None
   elif name=='same_sequence':f['sequence']=source['sequence']
   elif name=='changed_patch':im.paste('red',(985,551,1032,603))
   else:intent['intent']='build_route'
   result=check(intent,source,f,old,im,now);assert result['eligible'] is False;controls[name]=result
 inputs=[e for e in events if e['event']=='pointer_admission'];assert [e['operation'] for e in inputs]==['move','button_down']
 assert all(e['id']=='execute-menu-intent' and e['input_ack_ns']<d['guard']['valid_until_ns'] for e in inputs)
 terminals=[e for e in events if e['event']=='terminal'];assert all(e['status']=='completed' and e['release']['verified'] for e in terminals)
 assert sum(e['event']=='accepted' and e['id']=='execute-menu-intent' for e in events)==1
 assert read(run/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True}
 assert read(run/'evaluation.json')['contract_satisfied'] is False
 report={'events':len(events),'calls':len(state['calls']),'frames':len(obs),'old_observation_age_ms':d['old_observation_age_ms'],'fresh_capture_to_button_ack_ms':(inputs[-1]['input_ack_ns']-fresh['capture_ns'])/1e6,'fresh_capture_to_action_terminal_ms':(terminals[-1]['terminal_ns']-fresh['capture_ns'])/1e6,'model_usage':next(e['usage'] for e in me if e['type']=='turn.completed'),'controls':controls,'scope':'guided fixed menu intent with sampled exact patch; offline refusals, not live negative-input tests or broad semantic identity','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
