"""Actual screenshot/model Calc loop through the shared phased caller."""
import hashlib,json,subprocess,sys,tempfile,shutil,time
from pathlib import Path
from PIL import Image
from durable_submit_v4 import initialize,run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from append_checkpoint_v1 import load
from calc_proposal_schema_v1 import parse
from sampled_target_contract_v1 import evaluate
from phased_submit_v1 import execute
from decision_pair_v1 import collect
H=Path(__file__).resolve().parent;R=H/'results/sampled-effect-calc-02';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def win(p):return 'C:'+str(p.resolve())[6:]
names=['sampled_effect_calc_v2.py','phased_submit_v1.py','activation_handoff_v1.py','sampled_target_contract_v1.py','durable_submit_v4.py','calc_proposal_schema_v1.py','model_context_runner_v1.py','screenshot_responder_v1.txt','cause_servo_socket_v8.py','decision_pair_v1.py']
dump('plan.json',{'seed':238,'scope':'actual Calc screenshot proposals, shared phases, at most6 decisions; no automatic input replay','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,str(H/'cause_servo_socket_v8.py'),'calc','serve','--','--app','calc','--seed','238','--out',str(R/'runtime')],stdout=subprocess.PIPE,stderr=(R/'stderr.txt').open('w'),text=True)
temp=tempfile.TemporaryDirectory();journal=Path(temp.name)/'journal.jsonl';calls=[];turns=[]
saved_snapshots=[]
workbook_path=None
def locate_workbook():
 def descendants(pid):
  found=[]
  for child in Path(f'/proc/{pid}/task/{pid}/children').read_text().split():
   found.append(int(child));found.extend(descendants(int(child)))
  return found
 candidates=[]
 for pid in descendants(p.pid):
  argv=[b.decode() for b in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if b]
  if not argv or Path(argv[0]).name not in ('soffice.bin','oosplash','libreoffice','soffice'):continue
  for arg in argv[1:]:
   candidate=Path(arg)
   if candidate.name=='sheet.xlsx' and candidate.is_absolute():
    resolved=candidate.resolve(strict=True)
    assert resolved.parent.parent==Path('/tmp') and resolved.parent.name.startswith('realapp-x-')
    candidates.append({'pid':pid,'executable':argv[0],'path':str(resolved)})
 assert len({c['path'] for c in candidates})==1,'unique private descendant workbook required'
 dump('workbook-location.json',{'bridge_pid':p.pid,'candidates':candidates,'scope':'audit-only path, never provided to model'})
 return Path(candidates[0]['path'])
def saved_snapshot(label):
 entry={'label':label,'after_exchanges':len(calls),'begin_ns':time.perf_counter_ns(),'authority':'none; independent audit only, never planner evidence'}
 try:
  blob=workbook_path.read_bytes()
  entry['read_finished_ns']=time.perf_counter_ns()
  path=R/f'workbook-snapshot-{len(saved_snapshots):02d}.xlsx';path.write_bytes(blob)
  entry.update(file=path.name,sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob))
  entry['read_status']='bytes_copied_for_postrun_audit'
 except Exception as error:entry.update(read_status='unavailable',error=type(error).__name__,detail=str(error))
 entry['finished_ns']=time.perf_counter_ns();saved_snapshots.append(entry);dump('workbook-snapshots.json',saved_snapshots)

try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep)
 initial=request_once(ep['socket'],start(ep['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial);initialize(journal,initial['continuation'])
 goal=next(e['goal'] for e in initial['reply']['records'] if e['event']=='ready')
 workbook_path=locate_workbook()
 saved_snapshot('initial')
 def call(spec):
  begin=time.perf_counter_ns();r=run(journal,spec);calls.append({'begin_ns':begin,'end_ns':time.perf_counter_ns(),'result':r});dump('calls.json',calls);shutil.copy2(journal,R/'journal.jsonl');return r
 def clock():
  r=call({'command':{'op':'clock'},'timeout':3});assert r['state']['pending'] is None;return r['state']['last_resolution']['clock']
 feedback=None
 for index in range(1,7):
  state=load(journal);assert state['pending'] is None;source=state['continuation']['observation']
  prompt=f'''Control this isolated LibreOffice Calc worksheet from its screenshot. Goal: A1={goal['a']}, A2={goal['b']}, saved in existing sheet.xlsx using Excel format. Every act must start with one visually justified pointer click, followed only by keyboard steps. Click a cell to establish its target before typing. Stop after Save if a format dialog may open; only confirm a dialog that is visible. Interrupted actions may already have effects: inspect new evidence, never blindly replay. A click-only action is allowed. Each first click is checked against a fresh pixel patch; the keyboard tail receives a separate deadline after a sampled focus check. These checks do not prove widget identity.
Return ONLY one JSON object:
{{"kind":"act","steps":[...],"rationale":"short explanation"}}
{{"kind":"verify","visible_A1":INTEGER,"visible_A2":INTEGER,"confirmation_dialog_visible":BOOLEAN,"rationale":"short explanation"}}
{{"kind":"stop","rationale":"explanation"}}
Act has1..10 exact steps. First: {{"op":"pointer_click","x":INTEGER,"y":INTEGER,"duration_ms":80}}, bounds0..1279,0..799. Tail permits {{"op":"text","text":"1..8 ASCII digits"}}, {{"op":"key","key":"Return|Tab|Escape|Home|Up|Down|Left|Right"}}, {{"op":"chord","modifier":"Control_L","key":"s|a|Home"}}. No extra fields or tools; rationale1..600 characters. Verify only when both visible values match and no confirmation dialog remains; it requests independent saved-file scoring. Evidence: {json.dumps(feedback)}'''
  prompt_path=R/f'prompt-{index}.txt';prompt_path.write_text(prompt,encoding='utf-8');image=R/'runtime'/Path(source['image']).name
  begin=time.perf_counter_ns();m=subprocess.run(['/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe',win(H/'model_context_runner_v1.py'),'C:/Program Files/nodejs/node.exe','C:/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js',win(image),win(prompt_path),win(H.parent.parent),win(R/f'model-{index}'),'responder'],capture_output=True,timeout=90)
  (R/f'model-{index}-stdout.txt').write_bytes(m.stdout);(R/f'model-{index}-stderr.txt').write_bytes(m.stderr);assert m.returncode==0 and p.poll() is None
  events=[json.loads(l) for l in (R/f'model-{index}/events.jsonl').read_text(encoding='utf-8').splitlines()];items=[e['item'] for e in events if e['type']=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message'
  proposal=parse(items[0]['text']);row={'turn':index,'source':source,'feedback':feedback,'proposal':proposal,'model_begin_ns':begin,'model_end_ns':time.perf_counter_ns(),'calls_begin':len(calls)}
  dump(f'proposal-{index}.json',proposal)
  if proposal['kind']=='verify':
   assert (proposal['visible_A1'],proposal['visible_A2'],proposal['confirmation_dialog_visible'])==(goal['a'],goal['b'],False)
   turns.append(row);dump('turns.json',turns);break
  assert proposal['kind']=='act',proposal
  first=proposal['steps'][0];assert first['op']=='pointer_click'
  x,y=first['x'],first['y'];contract={'name':'calc-first-click','box':[max(0,x-12),max(0,y-12),min(1280,x+13),min(800,y+13)],'point':[x,y],'max_age_ms':1000}
  c=clock();fresh=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+3_000_000_000,'steps':[{'op':'observe'}]},'timeout':3});assert fresh['state']['pending'] is None
  o=fresh['state']['continuation']['observation'];c=clock()
  with Image.open(image) as old,Image.open(R/'runtime'/Path(o['image']).name) as new:checked=evaluate(contract,{'intent':contract['name'],'execute_once':True},source,o,old,new,c['runtime_ns'])
  row.update(contract=contract,fresh=o,clock=c,checked=checked)
  phases=execute(call,proposal,checked,o);row['phases']=phases;row['calls_end']=len(calls)
  turns.append(row);dump('turns.json',turns)
  state=load(journal);assert state['pending'] is None,'unresolved result requires explicit reconciliation'
  feedback={'proposal':proposal,'phase_status':phases['status'],'reason':phases.get('reason'),'target_check':checked,'resolution':state['last_resolution']}
  saved_snapshot(f'after-phase-{index}')
  sampling_begin=len(calls);sampling_started=time.perf_counter_ns()
  def decision_capture():
   c=clock()
   r=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+3_000_000_000,'steps':[{'op':'observe'}]},'timeout':3})
   assert r['state']['pending'] is None
   t=r['state']['last_resolution']['terminal']
   assert t['status']=='completed' and t['release']['verified'],'passive observation interrupted'
   o=r['state']['continuation']['observation'];c=clock()
   return {'observation':o,'image':str(R/'runtime'/Path(o['image']).name),'clock':c}
  o=state['continuation']['observation']
  samples=collect({'observation':o,'image':str(R/'runtime'/Path(o['image']).name)},decision_capture,3)
  row['decision_sampling']={'calls_begin':sampling_begin,'calls_end':len(calls),'elapsed_s':(time.perf_counter_ns()-sampling_started)/1e9,'result':samples}
  feedback['decision_samples']={'status':samples['status'],'additional_captures':len(samples['checks']),'scope':samples['scope'],'authority':'none'}
  dump('turns.json',turns)
  saved_snapshot(f'after-sampling-{index}')

 else:raise RuntimeError('decision limit; not completed')
 finish=request_once(ep['socket'],load(journal)['continuation'],{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish'});dump('finish.json',finish)
 evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');assert evaluation['success'] is True
 code=p.wait(timeout=10);assert code==0;dump('result.json',{'exit_code':code,'model_calls':index,'saved_success':True});print(json.dumps({'saved_success':True,'model_calls':index}))
except Exception as e:dump('error.json',{'type':type(e).__name__,'detail':str(e),'retry':False});raise
finally:
 if journal.exists():shutil.copy2(journal,R/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
