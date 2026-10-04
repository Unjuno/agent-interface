"""Audit bounded automatic model handoff against runtime and independent workbook."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from append_checkpoint_v1 import load,inspect
from received_continuation_v1 import start,advance
from calc_proposal_schema_v1 import parse
from timing_envelope_v1 import interval,validate
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/timing-envelope-calc-01';control=HERE/'results/timing-envelope-calc-control-01';runtime=r/'runtime'
 envelope_controls=HERE/'results/timing-envelope-controls-01'
 for n,h in read(envelope_controls/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 assert read(envelope_controls/'result.json')=={
     'same_process_interval':'comparable','missing_interval':'missing_endpoint',
     'different_domain_interval':'different_clock_domain','invalid_records_refused':6}
 for directory in (r,control):
  for n,h in read(directory/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(runtime/'sources.json').items():assert sha(HERE.parent/n)==h,n
 ep=read(r/'endpoint.json');events=[json.loads(l) for l in (runtime/'events.jsonl').read_text().splitlines()]
 state=start(ep['socket']);calls=read(r/'calls.json');assert len(calls)==8
 def replay(c):
  nonlocal state
  q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
  state=advance(state,ep['socket'],q['after'],a)
  assert state==(c['state']['continuation'] if 'state' in c else c['continuation'])
 initial=read(r/'initial.json');replay(initial)
 for c in calls:replay(c['result']);assert c['result']['state']['pending'] is None
 assert load(r/'journal.jsonl')==calls[-1]['result']['state'] and inspect(r/'journal.jsonl')[1]==17
 replay(read(r/'finish.json'))
 models=[];handoffs=read(control/'turns.json');assert len(handoffs)==3
 image=Path(initial['continuation']['observation']['image']).name
 for n in range(1,4):
  d=r/f'model-{n}';plan=read(d/'plan.json');process=read(d/'process.json')
  assert plan['requested_model']=='gpt-5.6-luna' and plan['requested_effort']=='low'
  assert plan['runner_sha256']==sha(HERE/'model_pair_runner_v1.py') and plan['image_sha256']==sha(runtime/image)
  assert (d/'prompt.txt').read_text(encoding='utf-8')==(r/f'prompt-{n}.txt').read_text(encoding='utf-8')
  assert process['exit_code']==0
  lines=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arrivals=[json.loads(l) for l in (d/'arrivals.jsonl').read_text().splitlines()]
  assert len(lines)==len(arrivals)
  for line,a in zip(lines,arrivals):assert sha_bytes(line)==a['sha256'] and len(line)==a['bytes']
  records=[json.loads(l) for l in lines];items=[e['item'] for e in records if e['type']=='item.completed']
  assert len(items)==1 and items[0]['type']=='agent_message'
  typed=parse(items[0]['text']);assert typed==read(r/f'typed-{n}.json')
  usage=next(e['usage'] for e in records if e['type']=='turn.completed')
  row={'turn':n,'kind':typed['kind'],'usage':usage,'runner_wall_ms':(process['exited_ns']-process['started_ns'])/1e6}
  if n<3:
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
 terms=[e for e in events if e['event']=='terminal'];assert len(terms)==4
 assert [(t['status'],t['steps_completed']) for t in terms]==[
     ('completed',1),('needs_decision',4),('completed',1),('needs_decision',0)]
 assert all(t['release']['verified'] is True and t['release']['buttons_down']==[] and t['release']['keys_down']==[] for t in terms)
 assert len([e for e in events if e['event']=='accepted'])==4 and not any(e['event']=='rejected' for e in events)
 commands=[e['command'] for e in events if e['event']=='command']
 assert len({c['transport_request_id'] for c in commands})==len(commands)
 saves=sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for c in commands for s in c.get('steps',[]));assert saves==1
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==12;decoder=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=decoder.accept((runtime/f'{n:03d}.ait').read_bytes())
  with Image.open(runtime/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 evaluation=next(e for e in events if e['event']=='independent_evaluation');assert evaluation['success'] is True
 wb=load_workbook(runtime/'sheet.xlsx',data_only=True);values=[wb.active['A1'].value,wb.active['A2'].value];wb.close();assert values==[480,192]
 result=read(control/'result.json');assert result['exit_code']==0 and result['success'] is True and read(r/'result.json')['exit_code']==0
 timing=[validate(json.loads(line)) for line in (control/'timing-envelope.jsonl').read_text().splitlines()]
 assert [row['sequence'] for row in timing]==list(range(1,len(timing)+1))
 observed=[row for row in timing if row['state']=='OBSERVED']
 assert len({row['clock']['domain_id'] for row in observed})==1
 missing=[row for row in timing if row['state']=='NOT_RECORDED']
 assert {row['event'] for row in missing}=={
     'runtime_receipt','os_injection','provider_request_received','provider_first_token'}
 def per_turn(event,turn):
  return next(row for row in timing if row['event']==event and row['details'].get('turn')==turn)
 measured=[]
 for turn in (1,2):
  model_interval=interval(per_turn('planner_request_started',turn),per_turn('planner_proposal_received',turn))
  feedback_interval=interval(per_turn('proposal_published',turn),per_turn('first_useful_feedback_detected',turn))
  assert model_interval['status']==feedback_interval['status']=='comparable'
  measured.append({'turn':turn,'model_ms':model_interval['duration_ns']/1e6,
                   'proposal_to_useful_feedback_ms':feedback_interval['duration_ns']/1e6,
                   'feedback_uncertainty_ms':feedback_interval['uncertainty_ns']/1e6})
 model_intervals=[interval(per_turn('planner_request_started',turn),
                           per_turn('planner_proposal_received',turn))
                  for turn in (1,2,3)]
 assert all(row['status']=='comparable' for row in model_intervals)
 feedback_to_next=[
     interval(per_turn('first_useful_feedback_detected',turn),
              per_turn('planner_request_started',turn+1))
     for turn in (1,2)]
 assert all(row['status']=='comparable' for row in feedback_to_next)
 first=next(row for row in timing if row['event']=='initial_observation_detected')
 final=next(row for row in timing if row['event']=='semantic_completion_detected')
 whole=interval(first,final);assert whole==result['initial_observation_to_semantic_completion']
 assert not (control/'error.json').exists() and not (r/'abort.json').exists()
 assert not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
 report={'events':len(events),'exact_frames':12,'append_records':17,'socket_calls':10,'model_turns':models,
         'save_chords':saves,'saved_cells':values,'xlsx_sha256':sha(runtime/'sheet.xlsx'),
         'supervisor_start_to_verified_exit_ms':(result['finished_ns']-result['started_ns'])/1e6,
         'linux_initial_capture_to_evaluation_ms':(evaluation['emit_started_ns']-obs[0]['capture_ns'])/1e6,
         'envelope_events':len(timing),'measured_turns':measured,
         'model_wait_total_ms':sum(row['duration_ns'] for row in model_intervals)/1e6,
         'feedback_to_next_planner_ms':[row['duration_ns']/1e6 for row in feedback_to_next],
         'initial_observation_to_semantic_completion_ms':whole['duration_ns']/1e6,
         'initial_to_completion_uncertainty_ms':whole['uncertainty_ns']/1e6,
         'missing_endpoints':sorted(row['event'] for row in missing),
         'scope':'one fresh automatic typed Calc episode with process-scoped supervisor timing; no matched speed ratio, OpenTTD coverage or human parity',
         'audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
if __name__=='__main__':main()
