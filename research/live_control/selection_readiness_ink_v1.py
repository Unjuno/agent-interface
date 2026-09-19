"""Live Inkscape reply abandonment followed by model-selected durable reconciliation."""
import hashlib,json,socket,subprocess,sys,time,tempfile,shutil
from pathlib import Path
from PIL import Image
from durable_submit_v4 import initialize,run
from recover_once_v1 import recover_once
from append_checkpoint_v1 import load
from received_continuation_v1 import start
from received_exchange_v2 import request_once
H=Path(__file__).resolve().parent;R=H/'results/selection-readiness-ink-01';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def win(p):return 'C:'+str(p.resolve())[6:]
names=['selection_readiness_ink_v1.py','durable_submit_v4.py','append_checkpoint_v1.py','received_continuation_v1.py','received_exchange_v2.py','cause_servo_socket_v7.py','model_context_runner_v1.py','screenshot_responder_v1.txt','recover_once_v1.py']
dump('plan.json',{'seed':239,'scope':'scripted initial edit and deliberate response abandonment; one bounded caller recovery read; scripted deselect/reselect then timed observations only; no model','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in names}})
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
 begin=time.perf_counter_ns();recovered=recover_once(journal,timeout=3);end=time.perf_counter_ns();calls.append({'begin_ns':begin,'end_ns':end,'result':recovered});dump('calls.json',calls);dump('recovered.json',recovered);assert recovered['state']['pending'] is None
 def program(steps):
  c=clock();return call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':steps},'timeout':3})
 program([{'op':'key','key':'Escape'},{'op':'key','key':'Escape'},{'op':'observe'}])
 selected=program([{'op':'pointer_click','x':664,'y':391,'duration_ms':80},{'op':'observe'}]);dump('selected.json',selected)
 epoch=time.perf_counter_ns();samples=[]
 def record(label,result):
  o=result['state']['continuation']['observation']
  with Image.open(R/'runtime'/Path(o['image']).name) as im:
   patch=im.crop([538,94,563,119]);pixels=patch.tobytes();color=patch.getpixel((12,12))
  samples.append({'label':label,'driver_elapsed_s':(time.perf_counter_ns()-epoch)/1e9,'observation':o,'patch_sha256':hashlib.sha256(pixels).hexdigest(),'center_pixel':color});dump('samples.json',samples)
 record('selected-result',selected)
 for offset in [0,.1,.25,.5,1,2,4,8]:
  delay=epoch+int(offset*1e9)-time.perf_counter_ns()
  if delay>0:time.sleep(delay/1e9)
  record(str(offset),program([{'op':'observe'}]))
 state=load(journal);live('after-passive-samples')
 finish=request_once(ep['socket'],state['continuation'],{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish-once'});dump('finish.json',finish);evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');assert evaluation['success'] is True
 code=p.wait(timeout=10);assert code==0;dump('result.json',{'exit_code':code,'success':True,'recovery_reads':1,'model_calls':0});print(json.dumps({'success':True,'model_calls':0}),flush=True)
except Exception as e:dump('error.json',{'type':type(e).__name__,'detail':str(e),'retry':False});raise
finally:
 if journal.exists():shutil.copy2(journal,R/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
