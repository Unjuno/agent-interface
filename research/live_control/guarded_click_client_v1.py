"""Explicit once-only guarded click: fresh observation, shared contract, owner admission."""
import hashlib,json,sys,time,uuid
from pathlib import Path
from PIL import Image
from sampled_target_contract_v1 import evaluate
from unix_json_deadline import exchange
HERE=Path(__file__).resolve().parent
socket,specfile,output=sys.argv[1:];out=Path(output);out.mkdir(exist_ok=False)
spec=json.loads(Path(specfile).read_text());previous=json.loads(Path(spec['previous_reply']).read_text());cursor=previous['cursor'];calls=[]
source=next(e for e in reversed(previous['records']) if e['event']=='observation')
def save(name,value):(out/name).write_text(json.dumps(value,indent=2)+'\n')
save('plan.json',{'spec':spec,'source_observation':source,'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('guarded_click_client_v1.py','sampled_target_contract_v1.py','unix_json_deadline.py')}})
def query(events,command):
 global cursor
 q={'after':cursor,'events':events,'timeout':2,'request_id':uuid.uuid4().hex,'command':command}
 t=time.perf_counter_ns();r=exchange(socket,q,timeout=5);calls.append({'request':q,'reply':r,'started_ns':t,'returned_ns':time.perf_counter_ns()});save('calls.json',calls);cursor=r['cursor']
 return r

def clock():return next(e for e in query(['clock'],{'op':'clock'})['records'] if e['event']=='clock')
c=clock();reply=query(['terminal'],{'op':'submit','id':spec['id']+'-observe','expected_sequence':c['sequence'],'valid_until_ns':c['runtime_ns']+30_000_000_000,'steps':[{'op':'observe'}]})
fresh=next(e for e in reversed(reply['records']) if e['event']=='observation');c=clock()
with Image.open(source['image']) as old,Image.open(fresh['image']) as new:decision=evaluate(spec['contract'],spec['intent'],source,fresh,old,new,c['runtime_ns'])
save('decision.json',{'decision':decision,'fresh_observation':fresh,'clock':c})
if decision['eligible']:
 reply=query(['terminal'],{'op':'submit','id':spec['id'],'expected_sequence':decision['expected_sequence'],'valid_until_ns':decision['valid_until_ns'],'steps':[{'op':'pointer_click','x':decision['point'][0],'y':decision['point'][1],'duration_ms':80},{'op':'observe'}]})
save('reply.json',reply)
print(json.dumps({'decision':decision,'cursor':cursor,'observations':[{k:e.get(k) for k in ('sequence','image','pointer_binding')} for e in reply['records'] if e['event']=='observation'],'terminals':[e for e in reply['records'] if e['event']=='terminal']}))
