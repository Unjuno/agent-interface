#!/usr/bin/env python3
import json,socket,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parents[1];UP=HERE/'upstream'
READ_TIMEOUT_S=0.30;EFFECT_DELAY_S=0.15

def recv_line(sock):
    data=b''
    while not data.endswith(b'\n'):
        chunk=sock.recv(65536)
        if not chunk:break
        data+=chunk
    return json.loads(data.decode())

def run_case(outdir:Path,case_id:str,policy:str,scope:str,producer_mode='effect'):
    outdir.mkdir(parents=True,exist_ok=False)
    action_id=f'action-{case_id}';request_id=f'request-{case_id}';telemetry=outdir/'producer.json'
    server='event_socket_v11.py' if policy=='endpoint_only' else 'event_socket_producer_ready_v1.py'
    args=[sys.executable,'-u',str(UP/server),'serve','--',producer_mode,action_id,request_id,str(telemetry),str(EFFECT_DELAY_S)]
    started_ns=time.perf_counter_ns()
    proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    first=proc.stdout.readline().strip();endpoint_received_ns=time.perf_counter_ns()
    if not first:
        stderr=proc.stderr.read();proc.kill();raise RuntimeError(f'no endpoint line: {stderr}')
    socket_record=json.loads(first);response=None
    if socket_record.get('event')=='observation_socket':
        req={'after':0,'events':['effect_evidence'],'timeout':READ_TIMEOUT_S}
        if scope=='action':req['action_id']=action_id
        elif scope=='request':req['read_request_id']=request_id
        else:raise ValueError(scope)
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
            s.settimeout(3);s.connect(socket_record['socket']);read_started_ns=time.perf_counter_ns();s.sendall((json.dumps(req)+'\n').encode());response=recv_line(s);read_returned_ns=time.perf_counter_ns()
    else:read_started_ns=read_returned_ns=None
    stdout_tail=proc.stdout.read();stderr=proc.stderr.read();code=proc.wait(timeout=5);proc.stdout.close();proc.stderr.close()
    producer=json.loads(telemetry.read_text()) if telemetry.exists() else None
    records=(response or {}).get('records',[])
    ready_records=[r for r in records if r.get('event')=='producer_ready']
    effect_records=[r for r in records if r.get('event')=='effect_evidence']
    row={
      'case_id':case_id,'policy':policy,'scope':scope,'producer_mode':producer_mode,
      'case_started_ns':started_ns,'endpoint_wait_ns':endpoint_received_ns-started_ns,
      'read_timeout_s':READ_TIMEOUT_S,'effect_delay_s':EFFECT_DELAY_S,
      'socket_event':socket_record.get('event'),'socket_authority':socket_record.get('authority'),
      'socket_readiness':socket_record.get('readiness'),'producer_ready_appended_ns':socket_record.get('producer_ready_appended_ns'),
      'endpoint_published_ns':socket_record.get('endpoint_published_ns'),'endpoint_received_ns':endpoint_received_ns,
      'status':(response or {}).get('status'),'response_authority':(response or {}).get('authority'),
      'record_count':len(records),'ready_record_count':len(ready_records),'effect_record_count':len(effect_records),
      'records':records,'effect_record':effect_records[-1] if effect_records else None,
      'read_started_ns':read_started_ns,'read_returned_ns':read_returned_ns,
      'read_elapsed_ns':None if read_started_ns is None else read_returned_ns-read_started_ns,
      'producer':producer,'server_code':code,'server_stdout_tail':stdout_tail,'server_stderr':stderr,
      'elapsed_ns':time.perf_counter_ns()-started_ns,
    }
    (outdir/'case.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    if response is not None:(outdir/'response.json').write_text(json.dumps(response,indent=2,sort_keys=True)+'\n')
    return row

if __name__=='__main__':
    if len(sys.argv) not in (5,6):raise SystemExit('usage: run_case.py OUT CASE POLICY SCOPE [MODE]')
    print(json.dumps(run_case(Path(sys.argv[1]),sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5] if len(sys.argv)==6 else 'effect'),sort_keys=True))
