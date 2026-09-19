"""Real held modifier expiry; verify release then passive snapshots without renewal."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
from received_continuation_v1 import start
from received_exchange_v2 import request_once
H=Path(__file__).resolve().parent;R=H/'results/expiry-observation-01';R.mkdir(exist_ok=False)
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
dump('plan.json',{'seed':240,'scope':'scripted real modifier hold expires, trailing text suppressed, passive release observations; no model or task-speed claim','sources':{n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ['probe_expiry_observation_v1.py','executor_v9.py','cause_servo_interactive_v6.py','cause_servo_socket_v8.py','post_release_observation_v2.py']}})
p=subprocess.Popen([sys.executable,str(H/'cause_servo_socket_v8.py'),'inkscape','serve','--','--app','inkscape','--seed','240','--out',str(R/'runtime')],stdout=subprocess.PIPE,stderr=(R/'stderr.txt').open('w'),text=True);calls=[]
try:
 ep=json.loads(p.stdout.readline());dump('endpoint.json',ep);state=start(ep['socket'])
 def call(spec):
  global state
  r=request_once(ep['socket'],state,spec);state=r['continuation'];calls.append(r);dump('calls.json',calls);return r
 call({'events':['observation'],'timeout':30});c=call({'events':['clock'],'timeout':3,'command':{'op':'clock'},'request_id':'expiry-clock'})['matched_clock']['record']
 r=call({'events':['terminal'],'timeout':3,'action_id':'expire-hold','request_id':'expire-once','command':{'op':'submit','id':'expire-hold','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+500000000,'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':1500},{'op':'text','text':'999'}]}})
 t=next(e for e in r['reply']['records'] if e['event']=='terminal');assert t['status']=='expired' and t['steps_completed']==0
 assert t['release']['verified'] is True and t['post_release_observation']['captures']==2
 assert state['observation']['capture_ns']>t['release']['verified_ns']
 call({'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish'})
 code=p.wait(timeout=10);assert code==0;dump('result.json',{'exit_code':code,'expected_expiry':True,'success_scope':'expiry/release observation, not edit task completion'});print(json.dumps({'expiry':True,'post_release_captures':2}))
finally:
 if p.poll() is None:p.terminate();p.wait(timeout=10)
