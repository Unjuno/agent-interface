"""Audit bounded automatic model handoff against runtime and independent workbook."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from append_checkpoint_v1 import load,inspect
from received_continuation_v1 import start,advance
from calc_proposal_schema_v1 import parse
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 label=sys.argv[1];r=HERE/'results'/label;control=HERE/'results'/(label+'-control');runtime=r/'runtime'
 mode=read(control/'plan.json')['history_mode'];count=read(control/'result.json')['model_turns']
 for directory in (r,control):
  for n,h in read(directory/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(runtime/'sources.json').items():assert sha(HERE.parent/n)==h,n
 ep=read(r/'endpoint.json');events=[json.loads(l) for l in (runtime/'events.jsonl').read_text().splitlines()]
 state=start(ep['socket']);calls=read(r/'calls.json');assert len(calls)==4*(count-1)
 def replay(c):
  nonlocal state
  q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
  state=advance(state,ep['socket'],q['after'],a)
  assert state==(c['state']['continuation'] if 'state' in c else c['continuation'])
 initial=read(r/'initial.json');replay(initial)
 for c in calls:replay(c['result']);assert c['result']['state']['pending'] is None
 assert load(r/'journal.jsonl')==calls[-1]['result']['state'] and inspect(r/'journal.jsonl')[1]==1+2*len(calls)
 replay(read(r/'finish.json'))
 models=[];handoffs=read(control/'turns.json');assert len(handoffs)==count
 image=Path(initial['continuation']['observation']['image']).name
 for n in range(1,count+1):
  d=r/f'model-{n}';plan=read(d/'plan.json');process=read(d/'process.json')
  assert plan['requested_tier']==read(control/'plan.json')['requested_tier'] and plan['observed_service_tier'] is None
  assert plan['requested_model']=='gpt-5.6-luna' and plan['requested_effort']=='low'
  assert plan['runner_sha256']==sha(HERE/'model_tier_runner_v1.py') and plan['image_sha256']==sha(runtime/image)
  assert (d/'prompt.txt').read_text(encoding='utf-8')==(r/f'prompt-{n}.txt').read_text(encoding='utf-8')
  history=read(r/'history.json');expected_history=history[max(0,n-2):n-1]
  prompt=(d/'prompt.txt').read_text(encoding='utf-8')
  assert json.loads(prompt.split('Previous proposals and runtime outcomes (historical evidence only): ')[1])==expected_history
  assert process['exit_code']==0
  lines=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arrivals=[json.loads(l) for l in (d/'arrivals.jsonl').read_text().splitlines()]
  assert len(lines)==len(arrivals)
  for line,a in zip(lines,arrivals):assert sha_bytes(line)==a['sha256'] and len(line)==a['bytes']
  records=[json.loads(l) for l in lines];items=[e['item'] for e in records if e['type']=='item.completed']
  assert len(items)==1 and items[0]['type']=='agent_message'
  typed=parse(items[0]['text']);assert typed==read(r/f'typed-{n}.json')
  usage=next(e['usage'] for e in records if e['type']=='turn.completed')
  row={'turn':n,'kind':typed['kind'],'usage':usage,'runner_wall_ms':(process['exited_ns']-process['started_ns'])/1e6}
  if n<count:
   proposal=read(r/f'proposal-{n}.json');assert proposal=={'steps':typed['steps'],'rationale':typed['rationale']}
   applied=read(r/f'applied-{n}.json');cs=calls[(n-1)*4:n*4]
   assert [c['result']['request']['command']['op'] for c in cs]==['clock','submit','clock','submit']
   assert cs[1]['result']['request']['command']['steps']==[{'op':'observe'}]
   assert cs[3]['result']['request']['command']['steps']==typed['steps']+[{'op':'observe'}]
   assert cs[3]['result']==applied['result']
   assert applied['fresh_observation']['sequence']>applied['source_observation']['sequence']
   assert applied['fresh_observation']['pointer_binding']==applied['source_observation']['pointer_binding']
   for cc,ac in [(cs[0],cs[1]),(cs[2],cs[3])]:
    clock=cc['result']['state']['last_resolution']['clock'];command=ac['result']['request']['command']
    assert command['expected_sequence']==clock['sequence'] and command['valid_until_ns']==clock['runtime_ns']+30_000_000_000
   image=Path(applied['result']['state']['continuation']['observation']['image']).name
   h=handoffs[n-1]
   row.update(supervisor_model_return_to_publish_ms=(h['proposal_published_ns']-h['model_runner_returned_ns'])/1e6,
              supervisor_publish_to_applied_ms=(h['applied_read_ns']-h['proposal_published_ns'])/1e6,
              linux_proposal_to_result_ms=(applied['returned_ns']-applied['proposal_received_ns'])/1e6,
              source_to_fresh_capture_ms=(applied['fresh_observation']['capture_ns']-applied['source_observation']['capture_ns'])/1e6)
  else:assert typed==read(r/'visual-verdict.json') and typed['kind']=='verify' and typed['visible_A1']==480 and typed['visible_A2']==192 and typed['confirmation_dialog_visible'] is False
  models.append(row)
 terms=[e for e in events if e['event']=='terminal'];assert len(terms)==2*(count-1)
 assert all(t['status'] in ('completed','needs_decision') for t in terms)
 assert all(t['release']['verified'] is True and t['release']['buttons_down']==[] and t['release']['keys_down']==[] for t in terms)
 assert len([e for e in events if e['event']=='accepted'])==2*(count-1) and not any(e['event']=='rejected' for e in events)
 commands=[e['command'] for e in events if e['event']=='command']
 assert len({c['transport_request_id'] for c in commands})==len(commands)
 saves=sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for c in commands for s in c.get('steps',[]));assert saves>=1
 obs=[e for e in events if e['event']=='observation'];assert len(obs)>=1;decoder=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=decoder.accept((runtime/f'{n:03d}.ait').read_bytes())
  with Image.open(runtime/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 evaluation=next(e for e in events if e['event']=='independent_evaluation');assert evaluation['success'] is True
 wb=load_workbook(runtime/'sheet.xlsx',data_only=True);values=[wb.active['A1'].value,wb.active['A2'].value];wb.close();assert values==[480,192]
 result=read(control/'result.json');assert result['exit_code']==0 and result['success'] is True and read(r/'result.json')['exit_code']==0
 assert not (control/'error.json').exists() and not (r/'abort.json').exists()
 assert not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
 report={'events':len(events),'exact_frames':len(obs),'append_records':1+2*len(calls),'socket_calls':len(calls)+2,'history_mode':mode,'requested_tier':read(control/'plan.json')['requested_tier'],'model_turns':models,
         'save_chords':saves,'saved_cells':values,'xlsx_sha256':sha(runtime/'sheet.xlsx'),
         'supervisor_start_to_verified_exit_ms':(result['finished_ns']-result['started_ns'])/1e6,
         'linux_initial_capture_to_evaluation_ms':(evaluation['emit_started_ns']-obs[0]['capture_ns'])/1e6,
         'scope':'one predeclared requested-tier comparison episode; current outcome only, no population/human parity claim',
         'audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
