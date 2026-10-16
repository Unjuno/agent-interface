"""Manual stage submissions over the private socket, with lossless state companion."""
import json
import sys
import uuid
import time
from bounded_followup_v2 import collect
from pathlib import Path
from unix_json_deadline import exchange
from early_exchange_v1 import run
from early_resume_v1 import resume
from decision_receipt_v5 import build as receipt
from input_state_table_v1 import build as table
from receipt_image import select_image
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent
stage,socket,directory=sys.argv[1:]
root=Path(directory);runtime=root/'runtime';out=root/stage;out.mkdir(exist_ok=False)
def save(name,value):
    (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def query(q):
    n=len(list(out.glob('query-*-request.json')));save(f'query-{n}-request',q)
    r=exchange(socket,q,timeout=16);save(f'query-{n}-reply',r);return r
if stage=='initial':
    save('plan',dict(seed=226,app='chromium',scope='One live self-use with executor v8 early response plus at most one bounded read in the same outer operation, full receipt and state table; no fault injection or speed comparison',
        model_tokens=None,verified_model_id=None,sources={n:digest((HERE/n).read_bytes()) for n in
        ['browser_combined_live_v1.py','cause_servo_socket_v5.py','cause_servo_interactive_v4.py','executor_v8.py','post_release_observation_v2.py',
         'input_state_table_v1.py','decision_receipt_v5.py','early_exchange_v1.py','early_resume_v1.py','bounded_followup_v2.py','stopped_client_v1.py','stopped_socket_v1.py','stopped_cursor_v1.py','stopped_scope_v1.py']}))
    batch=query(dict(after=0,events=['observation'],timeout=5));save('batch',batch)
    result=dict(batch=batch,image=select_image(batch,runtime))
else:
    spec=json.loads((root/(stage+'-input.json')).read_text())
    previous=root/spec['previous']
    batch=json.loads(previous.read_text())
    if 'last_reply' in batch:batch=batch['last_reply']
    if stage=='finish':
        result=query(dict(after=batch['cursor'],events=['independent_evaluation'],timeout=5,
                          request_id=uuid.uuid4().hex,command=dict(op='finish')))
    else:
        if spec.get('resume'):
            report=resume(query,json.loads(previous.read_text()),runtime)
        else:
            outer_started=time.perf_counter_ns()
            report=run(query,batch,runtime,stage,spec['steps'],30000,save)
            save('early-report',report)
            if report.get('state')=='input_stopped_capture_pending':
                report=collect(socket,report,runtime)
                attempt=report['exchanges'][-1]
                save('bounded-request',attempt['request'])
                if 'reply' in attempt:save('bounded-reply',attempt['reply'])
            report['outer_operation']=dict(started_ns=outer_started,prepared_ns=time.perf_counter_ns(),
                scope='through exchange and optional followup; report rendering and model receipt not included')
        save('report',report)
        data=(out/'report.json').read_bytes();review=receipt(data);states=table(data)
        save('receipt',review);save('state-table',states)
        result=dict(bounded_followup=report.get('bounded_followup'),outer_operation=report.get('outer_operation'),lifecycle=report.get('lifecycle'),receipt=review,state_table=states,image=report.get('image'))
save('result',result);print(json.dumps(result))
