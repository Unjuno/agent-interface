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
H=Path(__file__).resolve().parent;R=H/'results/sampled-decision-calc-01';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def win(p):return 'C:'+str(p.resolve())[6:]
names=['sampled_decision_calc_v1.py','phased_submit_v1.py','activation_handoff_v1.py','sampled_target_contract_v1.py','durable_submit_v4.py','calc_proposal_schema_v1.py','model_context_runner_v1.py','screenshot_responder_v1.txt','cause_servo_socket_v8.py','decision_pair_v1.py']
dump('plan.json',{'seed':238,'scope':'actual Calc screenshot proposals, shared phases, at most6 decisions; no automatic input replay','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,str(H/'cause_servo_socket_v8.py'),'calc','serve','--','--app','calc','--seed','238','--out',str(R/'runtime')],stdout=subprocess.PIPE,stderr=(R/'stderr.txt').open('w'),text=True)
temp=tempfile.TemporaryDirectory();journal=Path(temp.name)/'journal.jsonl';calls=[];turns=[]
try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep)
 initial=request_once(ep['socket'],start(ep['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial);initialize(journal,initial['continuation'])
 goal=next(e['goal'] for e in initial['reply']['records'] if e['event']=='ready')
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

 else:raise RuntimeError('decision limit; not completed')
 finish=request_once(ep['socket'],load(journal)['continuation'],{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish'});dump('finish.json',finish)
 evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');assert evaluation['success'] is True
 code=p.wait(timeout=10);assert code==0;dump('result.json',{'exit_code':code,'model_calls':index,'saved_success':True});print(json.dumps({'saved_success':True,'model_calls':index}))
except Exception as e:dump('error.json',{'type':type(e).__name__,'detail':str(e),'retry':False});raise
finally:
 if journal.exists():shutil.copy2(journal,R/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
