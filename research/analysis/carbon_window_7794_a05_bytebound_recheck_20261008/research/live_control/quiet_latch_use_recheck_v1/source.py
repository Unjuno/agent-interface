"""Cooperative condition source exposing a monotonic source version."""
import argparse,json,os,sys,time
p=argparse.ArgumentParser();p.add_argument('--scope',required=True);p.add_argument('--epoch',required=True);p.add_argument('--events',required=True);a=p.parse_args()
active=None;version=0
with open(a.events,'x',buffering=1) as log:
 def emit(event,**kw): log.write(json.dumps(dict(event=event,ns=time.perf_counter_ns(),pid=os.getpid(),**kw))+'\n')
 print(json.dumps(dict(ready=True,scope=a.scope,source_epoch=a.epoch,pid=os.getpid())),flush=True)
 for line in sys.stdin:
  req=json.loads(line);op=req['op']
  if op=='set':
   if type(req.get('active')) is not bool: raise ValueError('active bool required')
   active=req['active'];version+=1;out=dict(active=active,version=version)
  elif op=='query':
   q=req['request'];s=time.perf_counter_ns();v=active;e=time.perf_counter_ns()
   out=dict(scope=a.scope,producer_epoch=q['producer_epoch'],source_epoch=a.epoch,event_sequence=q['event_sequence'],request_id=q['request_id'],
            active=v,sample_start_ns=s,sample_end_ns=e,source_version=version)
  elif op=='recheck':
   q=req['request'];s=time.perf_counter_ns();v=version;e=time.perf_counter_ns()
   out=dict(scope=a.scope,producer_epoch=q['producer_epoch'],source_epoch=a.epoch,event_sequence=q['event_sequence'],request_id=q['request_id'],
            sample_start_ns=s,sample_end_ns=e,source_version=v)
  elif op=='finish': print(json.dumps(dict(finished=True)),flush=True);break
  else: raise ValueError('op')
  emit(op,request=req,reply=out);print(json.dumps(out),flush=True)
