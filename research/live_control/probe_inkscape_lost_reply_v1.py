"""Actual Inkscape command reply abandoned after write; read-only continuation recovery."""
import copy,hashlib,json,socket,subprocess,sys,time
from pathlib import Path
from received_continuation_v1 import start
from received_exchange_v2 import request_once
HERE=Path(__file__).resolve().parent
root=HERE/'results/inkscape-lost-reply-01';root.mkdir(exist_ok=False)
names=['probe_inkscape_lost_reply_v1.py','received_continuation_v1.py','received_exchange_v2.py','cause_servo_socket_v5.py','cause_servo_interactive_v4.py','stopped_socket_v1.py','command_once_v2.py','unix_json_deadline.py']
(root/'plan.json').write_text(json.dumps({'scope':'scripted real GUI command and deliberate response abandonment; no autonomous planning or model latency','seed':232,'expected_svg':{'x':88,'y':50,'width':40,'height':30},'expected_submissions':['select','move-save'],'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}},indent=2)+'\n')
p=subprocess.Popen([sys.executable,str(HERE/'cause_servo_socket_v5.py'),'inkscape','serve','--','--app','inkscape','--seed','232','--out',str(root/'runtime')],stdout=subprocess.PIPE,stderr=(root/'stderr.txt').open('w'),text=True)
state=None;calls=[]
def dump(name,data):(root/name).write_text(json.dumps(data,indent=2)+'\n')
try:
 endpoint=json.loads(p.stdout.readline());dump('endpoint.json',endpoint);state=start(endpoint['socket'])
 def call(spec):
  global state
  result=request_once(endpoint['socket'],state,spec);calls.append(result);state=result['continuation'];dump('calls.json',calls);dump('continuation.json',state);return result
 def clock(identifier):
  r=call({'events':['clock'],'timeout':2,'command':{'op':'clock'},'request_id':identifier})
  assert r['matched_clock'] is not None
  return r['matched_clock']['record']
 call({'events':['observation'],'timeout':30});c=clock('clock-select')
 call({'events':['terminal'],'timeout':3,'action_id':'select','request_id':'select-request','command':{'op':'submit','id':'select','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'pointer_click','x':619,'y':391,'duration_ms':80},{'op':'observe'}]}})
 c=clock('clock-save');prior=copy.deepcopy(state);dump('before-loss.json',prior)
 spec={'events':['terminal'],'timeout':3,'action_id':'move-save','request_id':'move-save-once','command':{'op':'submit','id':'move-save','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'pointer_click','x':550,'y':106,'duration_ms':80},{'op':'chord','modifier':'Control_L','key':'a'},{'op':'text','text':'88'},{'op':'key','key':'Return'},{'op':'chord','modifier':'Control_L','key':'s'},{'op':'observe'}]}}
 def abandon(path,q,**kwargs):
  dump('lost-request.json',q);payload=(json.dumps(q)+'\n').encode();began=time.perf_counter_ns()
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
   connection.settimeout(3);connection.connect(path);connection.sendall(payload)
   sent=time.perf_counter_ns()
  dump('loss.json',{'kind':'deliberate client close after sendall, before any recv','send_completed_ns':sent,'started_ns':began,'request_sha256':hashlib.sha256(payload).hexdigest(),'received_response_bytes':0,'server_receipt_at_close':'unknown','automatic_resend':False})
  raise ConnectionError('test client deliberately abandoned response')
 try:request_once(endpoint['socket'],state,spec,abandon)
 except ConnectionError:pass
 else:raise AssertionError('loss injection missing')
 assert state==prior and p.poll() is None
 recovered=None
 for _ in range(5):
  r=call({'events':['terminal'],'timeout':3,'action_id':'move-save'})
  if any(e['event']=='terminal' and e.get('id')=='move-save' for e in r['reply']['records']):recovered=r;break
 assert recovered is not None
 terminal=next(e for e in recovered['reply']['records'] if e['event']=='terminal' and e.get('id')=='move-save');assert terminal['status']=='completed',terminal
 dump('recovered.json',recovered)
 call({'events':['independent_evaluation'],'timeout':3,'command':{'op':'finish'},'request_id':'finish-once'})
 code=p.wait(timeout=10);assert code==0
 dump('result.json',{'exit_code':code,'calls_with_received_replies':len(calls),'lost_command_sent_once':True,'state_unchanged_on_loss':True,'scope':'scripted actual GUI and local connection abandonment, not organic network outage'})
 print(json.dumps({'exit_code':code,'calls':len(calls),'recovered_status':terminal['status']}))
finally:
 if p.poll() is None:
  p.terminate();p.wait(timeout=10)
