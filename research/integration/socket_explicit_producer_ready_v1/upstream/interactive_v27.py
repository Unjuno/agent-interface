"""Test-only producer for #807. No task/input authority."""
import json,sys,time
from pathlib import Path

# args: mode action_id request_id telemetry_path effect_delay_s
if len(sys.argv)!=6:raise SystemExit('expected mode action_id request_id telemetry_path effect_delay_s')
mode,action_id,request_id=sys.argv[1],sys.argv[2],sys.argv[3]
telemetry=Path(sys.argv[4]);delay=float(sys.argv[5])
start_ns=time.perf_counter_ns()
if mode=='silent':
    time.sleep(delay+0.45)
    telemetry.write_text(json.dumps({'mode':mode,'ready_emitted':False,'effect_emitted':False,'child_start_ns':start_ns},sort_keys=True)+'\n')
    raise SystemExit(0)
if mode=='malformed':
    malformed_ns=time.perf_counter_ns()
    print('{not-json',flush=True)
    telemetry.write_text(json.dumps({'mode':mode,'ready_emitted':False,'effect_emitted':False,'child_start_ns':start_ns,'malformed_ns':malformed_ns},sort_keys=True)+'\n')
    time.sleep(0.05);raise SystemExit(0)
if mode in ('wrong_ready','effect'):
    ready_ns=time.perf_counter_ns()
    ready={'event':'producer_ready','authority':'none' if mode=='effect' else 'invalid_authority','producer_ready_ns':ready_ns}
    print(json.dumps(ready,sort_keys=True),flush=True)
    if mode=='wrong_ready':
        telemetry.write_text(json.dumps({'mode':mode,'ready_emitted':True,'ready_authority':'invalid_authority','effect_emitted':False,'child_start_ns':start_ns,'producer_ready_ns':ready_ns},sort_keys=True)+'\n')
        time.sleep(delay+0.05);raise SystemExit(0)
else:raise SystemExit('bad mode')
time.sleep(delay)
effect_ns=time.perf_counter_ns()
record={
    'event':'effect_evidence',
    'final_program':action_id,
    'effect':{'action_id':action_id,'value':'ok'},
    'admitted_request':{'declared_action_id':action_id,'transport_request_id':request_id},
    'producer_effect_ns':effect_ns,
}
telemetry.write_text(json.dumps({'mode':mode,'ready_emitted':True,'ready_authority':'none','effect_emitted':True,'child_start_ns':start_ns,'producer_ready_ns':ready_ns,'producer_effect_ns':effect_ns},sort_keys=True)+'\n')
print(json.dumps(record,sort_keys=True),flush=True)
time.sleep(0.20)
