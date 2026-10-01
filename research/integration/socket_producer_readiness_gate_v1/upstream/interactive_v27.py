"""Test-only producer for #802. No task/input authority."""
import json,sys,time
from pathlib import Path

# args: mode action_id request_id telemetry_path delay_s
if len(sys.argv)!=6:raise SystemExit('expected mode action_id request_id telemetry_path delay_s')
mode,action_id,request_id=sys.argv[1],sys.argv[2],sys.argv[3]
telemetry=Path(sys.argv[4]);delay=float(sys.argv[5])
if mode=='silent':
    time.sleep(delay+0.45)
    telemetry.write_text(json.dumps({'mode':mode,'record_emitted':False},sort_keys=True)+'\n')
    raise SystemExit(0)
time.sleep(delay)
if mode=='malformed':
    emitted_ns=time.perf_counter_ns();telemetry.write_text(json.dumps({'mode':mode,'record_emitted':False,'malformed_written_ns':emitted_ns},sort_keys=True)+'\n')
    print('{not-json',flush=True);time.sleep(0.05);raise SystemExit(0)
if mode!='effect':raise SystemExit('bad mode')
emitted_ns=time.perf_counter_ns()
record={
    'event':'effect_evidence',
    'final_program':action_id,
    'effect':{'action_id':action_id,'value':'ok'},
    'admitted_request':{'declared_action_id':action_id,'transport_request_id':request_id},
    'producer_emitted_ns':emitted_ns,
}
telemetry.write_text(json.dumps({'mode':mode,'record_emitted':True,'producer_emitted_ns':emitted_ns},sort_keys=True)+'\n')
print(json.dumps(record,sort_keys=True),flush=True)
time.sleep(0.20)
