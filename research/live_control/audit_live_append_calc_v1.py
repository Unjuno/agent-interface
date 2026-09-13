"""Audit actual model proposals, journal continuations, GUI effects and separate clocks."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from received_continuation_v1 import start,advance
from append_checkpoint_v1 import load,inspect
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/live-append-calc-01';runtime=r/'runtime';ep=read(r/'endpoint.json')
 for n,h in read(r/'plan.json')['sources'].items():assert sha(HERE/n)==h,n
 for n,h in read(runtime/'sources.json').items():assert sha(HERE.parent/n)==h,n
 events=[json.loads(l) for l in (runtime/'events.jsonl').read_text().splitlines()]
 state=start(ep['socket']);calls=read(r/'calls.json');assert len(calls)==8
 def replay(c):
  nonlocal state
  q,a=c['request'],c['reply'];assert q['after']==state['cursor'] and a['records']==events[q['after']:a['cursor']]
  state=advance(state,ep['socket'],q['after'],a)
  assert state==(c['state']['continuation'] if 'state' in c else c['continuation'])
 replay(read(r/'initial.json'))
 for c in calls:
  replay(c['result']);assert c['result']['state']['pending'] is None
 assert load(r/'journal.jsonl')==calls[-1]['result']['state'] and inspect(r/'journal.jsonl')[1]==17
 replay(read(r/'finish.json'))
 model=[];outputs=[]
 for n,image in [(1,'001.png'),(2,'007.png'),(3,'012.png')]:
  d=r/f'model-{n}';plan=read(d/'plan.json');process=read(d/'process.json')
  assert plan['requested_model']=='gpt-5.6-luna' and plan['requested_effort']=='low'
  assert plan['runner_sha256']==sha(HERE/'model_pair_runner_v1.py')
  assert plan['image_sha256']==sha(runtime/image)
  assert (d/'prompt.txt').read_text(encoding='utf-8')==(r/f'prompt-{n}.txt').read_text(encoding='utf-8')
  assert process['exit_code']==0
  raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True)
  arrivals=[json.loads(l) for l in (d/'arrivals.jsonl').read_text().splitlines()]
  assert len(raw)==len(arrivals)
  for line,a in zip(raw,arrivals):assert hashlib.sha256(line).hexdigest()==a['sha256'] and len(line)==a['bytes']
  es=[json.loads(l) for l in raw];messages=[e['item'] for e in es if e['type']=='item.completed']
  assert len(messages)==1 and messages[0]['type']=='agent_message'
  proposal=json.loads(messages[0]['text']);outputs.append(proposal)
  usage=next(e['usage'] for e in es if e['type']=='turn.completed')
  model.append({'turn':n,'usage':usage,'runner_wall_ms':(process['exited_ns']-process['started_ns'])/1e6,'actual_served_identity':None,'cost':None})
  if n<=2:assert proposal==read(r/f'proposal-{n}.json')
 assert outputs[2]==read(r/'visual-verdict.json') and outputs[2]['next_action']=='request_independent_verification'
 timings=[]
 for n,offset in [(1,0),(2,4)]:
  a=read(r/f'applied-{n}.json');c= calls[offset:offset+4]
  assert [x['result']['request']['command']['op'] for x in c]==['clock','submit','clock','submit']
  assert c[1]['result']['request']['command']['steps']==[{'op':'observe'}]
  assert c[3]['result']['request']['command']['steps']==outputs[n-1]['steps']+[{'op':'observe'}]
  assert c[3]['result']==a['result']
  assert a['fresh_observation']['sequence']>a['source_observation']['sequence']
  assert a['fresh_observation']['pointer_binding']==a['source_observation']['pointer_binding']
  for clock_call,action_call in [(c[0],c[1]),(c[2],c[3])]:
   clk=clock_call['result']['state']['last_resolution']['clock'];cmd=action_call['result']['request']['command']
   assert cmd['expected_sequence']==clk['sequence'] and cmd['valid_until_ns']==clk['runtime_ns']+30_000_000_000
  timings.append({'proposal':n,'source_to_revalidation_capture_ms':(a['fresh_observation']['capture_ns']-a['source_observation']['capture_ns'])/1e6,
                  'four_api_calls_ms':sum(x['end_ns']-x['begin_ns'] for x in c)/1e6,
                  'proposal_received_to_result_ms':(a['returned_ns']-a['proposal_received_ns'])/1e6})
 terms=[e for e in events if e['event']=='terminal'];assert len(terms)==4
 assert [t['status'] for t in terms]==['completed','needs_decision','completed','needs_decision']
 assert all(t['release']['verified'] is True and t['release']['buttons_down']==[] and t['release']['keys_down']==[] for t in terms)
 assert all(t['decision_reason']=='focus_changed' for t in terms if t['status']=='needs_decision')
 assert len([e for e in events if e['event']=='accepted'])==4 and not any(e['event']=='rejected' for e in events)
 obs=[e for e in events if e['event']=='observation'];assert len(obs)==12
 dec=Decoder('live-control')
 for n,e in enumerate(obs,1):
  f=dec.accept((runtime/f'{n:03d}.ait').read_bytes())
  with Image.open(runtime/Path(e['image']).name) as im:assert (im.width,im.height,im.mode,im.tobytes())==(f.width,f.height,f.mode,f.pixels)
 evaluation=next(e for e in events if e['event']=='independent_evaluation');assert evaluation['success'] is True
 wb=load_workbook(runtime/'sheet.xlsx',data_only=True);values=[wb.active['A1'].value,wb.active['A2'].value];wb.close();assert values==[480,192]
 assert read(r/'result.json')['exit_code']==0 and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
 report={'events':len(events),'exact_frames':len(obs),'journal_records':17,'model_turns':model,'runtime_timings':timings,'saved_cells':values,
         'xlsx_sha256':sha(runtime/'sheet.xlsx'),'initial_capture_to_evaluation_ms':(evaluation['emit_started_ns']-obs[0]['capture_ns'])/1e6,
         'scope':'actual requested Luna screenshot proposals, assistant review/file handoff; independent success, no autonomous-loop or human-speed claim; Windows/Linux clocks never subtracted',
         'audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
