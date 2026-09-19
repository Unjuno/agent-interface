"""Live Inkscape reply abandonment followed by model-selected durable reconciliation."""
import hashlib,json,socket,subprocess,sys,time,tempfile,shutil
from pathlib import Path
from PIL import Image
from sampled_target_contract_v1 import evaluate
from durable_submit_v4 import initialize,run
from recover_once_v2 import recover_once
from recovery_view_v1 import present
from calc_proposal_schema_v1 import parse as parse_action
from append_checkpoint_v1 import load
from received_continuation_v1 import start
from received_exchange_v2 import request_once
H=Path(__file__).resolve().parent;R=H/'results/recovery-target-ink-01';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def win(p):return 'C:'+str(p.resolve())[6:]
names=['recovery_target_ink_v1.py','durable_submit_v4.py','append_checkpoint_v1.py','received_continuation_v1.py','received_exchange_v2.py','cause_servo_socket_v7.py','model_context_runner_v1.py','screenshot_responder_v1.txt','recover_once_v1.py','recover_once_v2.py','recovery_view_v1.py','calc_proposal_schema_v1.py','sampled_target_contract_v1.py']
dump('plan.json',{'seed':239,'scope':'scripted initial edit and deliberate response abandonment; one bounded caller recovery read; model chooses new X104 edit after recovered X88, then verification; one episode','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,str(H/'cause_servo_socket_v7.py'),'inkscape','serve','--','--app','inkscape','--seed','239','--out',str(R/'runtime')],stdout=subprocess.PIPE,stderr=(R/'stderr.txt').open('w'),text=True)
temp=tempfile.TemporaryDirectory(prefix='agent-interface-model-recovery-');journal=Path(temp.name)/'journal.jsonl';calls=[];lives=[]
def live(stage):
 status=p.poll();lives.append({'stage':stage,'poll':status,'pid':p.pid,'ns':time.perf_counter_ns()});dump('live.json',lives);assert status is None
try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep)
 initial=request_once(ep['socket'],start(ep['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial);initialize(journal,initial['continuation'])
 def call(spec):
  begin=time.perf_counter_ns();r=run(journal,spec);calls.append({'begin_ns':begin,'end_ns':time.perf_counter_ns(),'result':r});dump('calls.json',calls);shutil.copy2(journal,R/'journal.jsonl');return r
 def clock():return call({'command':{'op':'clock'},'timeout':3})['state']['last_resolution']['clock']
 c=clock();call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'pointer_click','x':619,'y':391,'duration_ms':80},{'op':'observe'}]},'timeout':3})
 c=clock();before=load(journal);dump('before-loss.json',before)
 spec={'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'pointer_click','x':550,'y':106,'duration_ms':80},{'op':'chord','modifier':'Control_L','key':'a'},{'op':'text','text':'88'},{'op':'key','key':'Return'},{'op':'chord','modifier':'Control_L','key':'s'},{'op':'observe'}]},'timeout':3};dump('edit-spec.json',spec)
 def abandon(path,q,**kwargs):
  payload=(json.dumps(q)+'\n').encode();dump('lost-request.json',q)
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
   s.settimeout(3);s.connect(path);s.sendall(payload)
  dump('loss.json',{'send_completed_ns':time.perf_counter_ns(),'received_response_bytes':0,'sha256':hashlib.sha256(payload).hexdigest(),'scope':'deliberate close after sendall before recv; not organic failure'})
  raise ConnectionError('deliberate reply abandonment')
 try:run(journal,spec,abandon)
 except ConnectionError:pass
 else:raise AssertionError('missing loss')
 pending=load(journal);dump('pending.json',pending);assert pending['pending'] is not None and pending['continuation']==before['continuation'];live('pending')
 def forbidden(*a,**k):raise AssertionError('new input reached transport while pending')
 try:run(journal,{'command':{'op':'clock'}},forbidden)
 except ValueError as e:assert str(e)=='unresolved command; read only';dump('blocked.json',{'error':str(e),'transport_called':False})
 else:raise AssertionError('not blocked')
 assert load(journal)==pending
 action=pending['pending']['request']['command']['id'];model_times=[]
 def model(n,observation,evidence):
  prompt='You control the selected rectangle in an isolated Inkscape task. Final goal: X=104,Y=50,W=40,H=30, saved in existing shape.svg. An earlier intermediate edit to X88 was sent with a lost response; the supplied evidence describes its reconciliation. That intermediate result is not final task completion. Inspect the current screenshot and evidence to choose a NEW bounded edit if needed. Never replay unresolved input or infer current target identity from old capture metadata. Return ONLY one JSON object: {"kind":"act","steps":[...],"rationale":"short explanation"}, {"kind":"verify","visible_x":NUMBER,"visible_y":NUMBER,"visible_width":NUMBER,"visible_height":NUMBER,"rationale":"short explanation"}, or {"kind":"stop","rationale":"explanation"}. Act allows1..10 exact steps: {"op":"pointer_click","x":INTEGER,"y":INTEGER,"duration_ms":80}; {"op":"text","text":"ASCII digits,1..8"}; {"op":"key","key":"Return|Tab|Escape|Home|Up|Down|Left|Right"}; {"op":"chord","modifier":"Control_L","key":"s|a|Home"}. Pointer bounds0..1279,0..799; rationale1..600 characters, no extra fields. A fresh observation and focus/binding check precede a new input, but do not prove semantic targeting. Verify requests independent saved artifact scoring only when the visible final geometry matches. No tools. Proposing an action is not execution. Evidence: '+json.dumps(evidence)
  prompt_path=R/f'prompt-{n}.txt';prompt_path.write_text(prompt,encoding='utf-8');image=R/'runtime'/Path(observation['image']).name
  args=['/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe',win(H/'model_context_runner_v1.py'),r'C:/Program Files/nodejs/node.exe',r'C:/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js',win(image),win(prompt_path),win(H.parent.parent),win(R/f'model-{n}'),'responder']
  begin=time.perf_counter_ns();m=subprocess.run(args,capture_output=True,timeout=90);end=time.perf_counter_ns();(R/f'model-{n}-stdout.txt').write_bytes(m.stdout);(R/f'model-{n}-stderr.txt').write_bytes(m.stderr);assert m.returncode==0
  records=[json.loads(l) for l in (R/f'model-{n}'/'events.jsonl').read_text(encoding='utf-8').splitlines()];items=[e['item'] for e in records if e['type']=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message'
  proposal=json.loads(items[0]['text']);dump(f'proposal-{n}.json',proposal);model_times.append({'turn':n,'begin_ns':begin,'end_ns':end});dump('model-times.json',model_times);live('after-model-'+str(n));return proposal
 begin=time.perf_counter_ns();recovered=recover_once(journal,timeout=3);end=time.perf_counter_ns()
 calls.append({'begin_ns':begin,'end_ns':end,'result':recovered});dump('calls.json',calls);shutil.copy2(journal,R/'journal.jsonl')
 assert 'command' not in recovered['request'];state=recovered['state'];assert state['pending'] is None and state['last_resolution']['terminal']['status']=='completed';dump('recovered.json',recovered)
 q=model(1,state['continuation']['observation'],recovered['recovery'])
 q=parse_action(json.dumps(q));assert q['kind']=='act'
 source=state['continuation']['observation']
 first=q['steps'][0];assert first['op']=='pointer_click' and 508<=first['x']<606 and 90<=first['y']<123
 contract={'name':'selected-rectangle-x-field','box':[508,90,606,123],'point':[first['x'],first['y']],'max_age_ms':1000}
 dump('contract.json',contract)
 # Deliberate same-application selection change after model return.
 c=clock();fault=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'key','key':'Escape'},{'op':'key','key':'Escape'},{'op':'observe'}]},'timeout':3});dump('target-fault.json',fault)
 c=clock();fresh=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]},'timeout':3})
 observation=fresh['state']['continuation']['observation'];c=clock()
 with Image.open(R/'runtime'/Path(source['image']).name) as old,Image.open(R/'runtime'/Path(observation['image']).name) as new:
  verdict=evaluate(contract,{'intent':contract['name'],'execute_once':True},source,observation,old,new,c['runtime_ns'])
 dump('target-verdict.json',{'source':source,'fresh':observation,'clock':c,'verdict':verdict,'proposal':q,'proposal_submitted':False})
 assert source['pointer_binding']==observation['pointer_binding'],'fault changed binding rather than same-focus target'
 assert verdict['eligible'] is False and verdict['reason']=='target_patch_changed',verdict
 state=load(journal)
 finish=request_once(ep['socket'],state['continuation'],{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish-once'});dump('finish.json',finish);evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');assert evaluation['success'] is True
 code=p.wait(timeout=10);assert code==0;dump('result.json',{'exit_code':code,'success':True,'final_goal_achieved':False,'expected_refusal':True,'recovery_reads':1,'model_calls':1});print(json.dumps({'success':True,'model_calls':1}),flush=True)
except Exception as e:dump('error.json',{'type':type(e).__name__,'detail':str(e),'retry':False});raise
finally:
 if journal.exists():shutil.copy2(journal,R/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
