"""Real focus change after activation, using the shared caller unchanged."""
import hashlib,json,subprocess,sys,tempfile,shutil,time
from pathlib import Path
from PIL import Image
from Xlib import X,display
from durable_submit_v4 import initialize,run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from append_checkpoint_v1 import load
from passive_pair_v1 import collect
from phased_submit_v1 import execute

H=Path(__file__).resolve().parent;R=H/'results/phased-focus-01';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
names=['probe_phased_focus_v1.py','phased_submit_v1.py','activation_handoff_v1.py','passive_pair_v1.py','sampled_target_contract_v1.py','durable_submit_v4.py','cause_servo_socket_v8.py']
dump('plan.json',{'scope':'scripted activation and private Xvfb focus fault; no model; no task success claim','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in names}})
p=subprocess.Popen([sys.executable,str(H/'cause_servo_socket_v8.py'),'inkscape','serve','--','--app','inkscape','--seed','240','--out',str(R/'runtime')],stdout=subprocess.PIPE,stderr=(R/'stderr.txt').open('w'),text=True)
temp=tempfile.TemporaryDirectory();journal=Path(temp.name)/'journal.jsonl';calls=[];controller=None;sink=None;original=None
try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep)
 initial=request_once(ep['socket'],start(ep['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial);initialize(journal,initial['continuation'])
 def call(spec):
  r=run(journal,spec);calls.append(r);dump('calls.json',calls);shutil.copy2(journal,R/'journal.jsonl');return r
 def clock():return call({'command':{'op':'clock'},'timeout':3})['state']['last_resolution']['clock']
 c=clock();selected=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+3_000_000_000,'steps':[{'op':'pointer_click','x':619,'y':391,'duration_ms':80},{'op':'observe'}]},'timeout':3})
 contract={'name':'x-field','box':[538,94,563,119],'point':[550,106],'max_age_ms':1000}
 def sample():
  c=clock();r=call({'command':{'op':'submit','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+3_000_000_000,'steps':[{'op':'observe'}]},'timeout':3});o=r['state']['continuation']['observation'];c=clock()
  return {'observation':o,'image':str(R/'runtime'/Path(o['image']).name),'clock':c}
 o=selected['state']['continuation']['observation']
 ready=collect({'observation':o,'image':str(R/'runtime'/Path(o['image']).name)},sample,contract,3);dump('readiness.json',ready);assert ready['stable']
 checked=ready['checks'][-1]['verdict'];source=ready['checks'][-1]['fresh']
 def descendants(pid):
  out=[]
  for child in Path(f'/proc/{pid}/task/{pid}/children').read_text().split():out.append(int(child));out.extend(descendants(int(child)))
  return out
 displays=[]
 for pid in descendants(p.pid):
  argv=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
  if argv and Path(argv[0].decode()).name=='Xvfb':displays.append(argv[1].decode())
 assert len(displays)==1
 controller=display.Display(displays[0]);original=controller.get_input_focus().focus
 injected=False
 def fault_call(spec):
  global injected,sink
  r=call(spec)
  if not injected and spec['command']['op']=='submit':
   t=r['state']['last_resolution']['terminal'];assert t['status']=='completed' and t['release']['verified']
   sink=controller.screen().root.create_window(0,0,100,80,0,controller.screen().root_depth,override_redirect=True)
   sink.map();sink.set_input_focus(X.RevertToParent,X.CurrentTime);controller.sync();injected=True
   dump('fault.json',{'activation_id':t['id'],'terminal_ns':t['terminal_ns'],'injected_ns':time.perf_counter_ns(),'focus_after':controller.get_input_focus().focus.id,'sink':sink.id,'display':displays[0]})
  return r
 proposal={'kind':'act','steps':[{'op':'pointer_click','x':550,'y':106,'duration_ms':80},{'op':'chord','modifier':'Control_L','key':'a'},{'op':'text','text':'104'},{'op':'key','key':'Return'},{'op':'chord','modifier':'Control_L','key':'s'}],'rationale':'scripted attempt to change selected rectangle X to104'}
 dump('input.json',{'proposal':proposal,'checked':checked,'source':source,'calls_begin':len(calls),'contract':contract})
 result=execute(fault_call,proposal,checked,source);dump('phases.json',result)
 assert result['reason']=='handoff_refused' and result['tail_submitted'] is False
 assert result['handoff']['verdict']['reason']=='binding_changed_or_missing'
 original.set_input_focus(X.RevertToParent,X.CurrentTime);sink.destroy();sink=None;controller.sync();controller.close();controller=None
 state=load(journal)
 finish=request_once(ep['socket'],state['continuation'],{'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish'});dump('finish.json',finish)
 code=p.wait(timeout=10);assert code==0
 dump('result.json',{'exit_code':code,'expected_refusal':True,'final_goal_achieved':False,'model_calls':0});print('real inter-phase focus change refused; no keyboard tail')
except Exception as e:dump('error.json',{'type':type(e).__name__,'detail':str(e)});raise
finally:
 if controller is not None:
  if original is not None:original.set_input_focus(X.RevertToParent,X.CurrentTime)
  if sink is not None:sink.destroy()
  controller.sync();controller.close()
 if journal.exists():shutil.copy2(journal,R/'journal.jsonl')
 if p.poll() is None:p.terminate();p.wait(timeout=10)
 temp.cleanup()
