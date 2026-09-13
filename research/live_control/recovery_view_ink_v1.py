"""Live Inkscape reply abandonment followed by model-selected durable reconciliation."""
import hashlib,json,socket,subprocess,sys,time,tempfile,shutil
from pathlib import Path
from durable_submit_v4 import initialize,run
from recover_once_v2 import recover_once
from append_checkpoint_v1 import load
from received_continuation_v1 import start
from received_exchange_v2 import request_once
H=Path(__file__).resolve().parent;R=H/'results/recovery-view-ink-01';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def win(p):return 'C:'+str(p.resolve())[6:]
names=['recovery_view_ink_v1.py','durable_submit_v4.py','append_checkpoint_v1.py','received_continuation_v1.py','received_exchange_v2.py','cause_servo_socket_v7.py','model_context_runner_v1.py','screenshot_responder_v1.txt','recover_once_v1.py','recover_once_v2.py','recovery_view_v1.py']
dump('plan.json',{'seed':239,'scope':'scripted initial edit and deliberate response abandonment; one bounded caller recovery read; model chooses verification only; one live episode','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in names}})
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
  prompt='You propose the next step for an isolated Inkscape task: X=88,Y=50,W=40,H=30 and existing shape.svg saved. An edit/save program was sent and its response abandoned. Use supplied evidence and image; a pre-send image is stale. Do not replay unresolved input. Return ONLY one JSON object: {"kind":"read","action_id":"EXACT pending action id","rationale":"explanation"} for command-free reconciliation; {"kind":"verify","visible_x":NUMBER,"visible_y":NUMBER,"visible_width":NUMBER,"visible_height":NUMBER,"rationale":"explanation"} to request independent artifact verification after received completion and matching visible geometry; or {"kind":"stop","rationale":"explanation"}. No tools. Neither sendall nor visual values alone prove resolved execution or saved success. Evidence: '+json.dumps(evidence)
  prompt_path=R/f'prompt-{n}.txt';prompt_path.write_text(prompt,encoding='utf-8');image=R/'runtime'/Path(observation['image']).name
  args=['/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe',win(H/'model_context_runner_v1.py'),r'C:/Program Files/nodejs/node.exe',r'C:/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js',win(image),win(prompt_path),win(H.parent.parent),win(R/f'model-{n}'),'responder']
  begin=time.perf_counter_ns();m=subprocess.run(args,capture_output=True,timeout=90);end=time.perf_counter_ns();(R/f'model-{n}-stdout.txt').write_bytes(m.stdout);(R/f'model-{n}-stderr.txt').write_bytes(m.stderr);assert m.returncode==0
  records=[json.loads(l) for l in (R/f'model-{n}'/'events.jsonl').read_text(encoding='utf-8').splitlines()];items=[e['item'] for e in records if e['type']=='item.completed'];assert len(items)==1 and items[0]['type']=='agent_message'
  proposal=json.loads(items[0]['text']);dump(f'proposal-{n}.json',proposal);model_times.append({'turn':n,'begin_ns':begin,'end_ns':end});dump('model-times.json',model_times);live('after-model-'+str(n));return proposal
 begin=time.perf_counter_ns();recovered=recover_once(journal,timeout=3);end=time.perf_counter_ns()
 calls.append({'begin_ns':begin,'end_ns':end,'result':recovered});dump('calls.json',calls);shutil.copy2(journal,R/'journal.jsonl')
 assert 'command' not in recovered['request'];state=recovered['state'];assert state['pending'] is None and state['last_resolution']['terminal']['status']=='completed';dump('recovered.json',recovered)
 q=model(1,state['continuation']['observation'],recovered['recovery'])
 assert set(q)=={'kind','visible_x','visible_y','visible_width','visible_height','rationale'} and q['kind']=='verify'
 assert [q[k] for k in ['visible_x','visible_y','visible_width','visible_height']]==[88,50,40,30]
 finish=request_once(ep['socket'],state['continuation'],{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish-once'});dump('finish.json',finish);evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');assert evaluation['success'] is True
 code=p.wait(timeout=10);assert code==0;dump('result.json',{'exit_code':code,'success':True,'recovery_reads':1,'model_calls':1});print(json.dumps({'success':True,'model_calls':1}),flush=True)
except Exception as e:dump('error.json',{'type':type(e).__name__,'detail':str(e),'retry':False});raise
finally:
 if journal.exists():shutil.copy2(journal,R/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
