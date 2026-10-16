"""Persist one explicit exchange with independent image and event continuation."""
import argparse,json,sys,time,uuid
from pathlib import Path
from received_continuation_v1 import start,advance,clock_for,read_request
from unix_json_deadline import exchange

def request_once(socket,state,spec,call=exchange):
 if set(spec)-{'events','timeout','command','request_id','clock_request_id','action_id'}:raise ValueError('unknown request option')
 q=read_request(state,spec['events'],spec.get('timeout',2))
 if 'action_id' in spec:q['action_id']=spec['action_id']
 if 'command' in spec:q.update(command=spec['command'],request_id=spec.get('request_id') or uuid.uuid4().hex)
 requested=spec.get('clock_request_id')
 if q.get('command',{}).get('op')=='clock':requested=q['request_id']
 reply=call(socket,q,timeout=min(35,q['timeout']+3))
 updated=advance(state,socket,q['after'],reply)
 return {'request':q,'reply':reply,'continuation':updated,'requested_clock_id':requested,
         'matched_clock':clock_for(updated,requested) if requested else None,
         'authority':'none; current observation and admission still required'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('socket');ap.add_argument('checkpoint');ap.add_argument('spec');ap.add_argument('out',type=Path);a=ap.parse_args()
 state=start(a.socket) if a.checkpoint=='-' else json.loads(Path(a.checkpoint).read_text())
 spec=json.loads(Path(a.spec).read_text());a.out.mkdir(exist_ok=False)
 (a.out/'input.json').write_text(json.dumps({'continuation':state,'spec':spec},indent=2)+'\n')
 # Persist raw network evidence even if continuation validation subsequently refuses it.
 def recorded(socket,q,**kwargs):
  (a.out/'request.json').write_text(json.dumps(q,indent=2)+'\n');begin=time.perf_counter_ns()
  try:r=exchange(socket,q,**kwargs)
  except Exception as error:
   (a.out/'error.json').write_text(json.dumps({'type':type(error).__name__,'detail':str(error),'command_may_have_been_forwarded':'command' in q,'automatic_retry':False})+'\n');raise
  (a.out/'reply.json').write_text(json.dumps(r,indent=2)+'\n');(a.out/'timing.json').write_text(json.dumps({'start_ns':begin,'returned_ns':time.perf_counter_ns()})+'\n');return r
 result=request_once(a.socket,state,spec,recorded)
 (a.out/'continuation.json').write_text(json.dumps(result['continuation'],indent=2)+'\n');(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 obs=result['continuation']['observation']
 print(json.dumps({'status':result['reply']['status'],'cursor':result['continuation']['cursor'],'observation':obs,'requested_clock_id':result['requested_clock_id'],'matched_clock':result['matched_clock'],'authority':'none'}))
if __name__=='__main__':main()
