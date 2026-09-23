"""Manual stage submissions over the private socket, with lossless state companion."""
import json
import sys
import uuid
from pathlib import Path
from unix_json_deadline import exchange
from pointer_exchange_v1 import run
from decision_receipt_v4 import build as receipt
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
    save('plan',dict(seed=225,app='calc',scope='One live self-use with executor v7 passive post-release observation, full receipt and state table; no fault injection or speed comparison',
        model_tokens=None,verified_model_id=None,sources={n:digest((HERE/n).read_bytes()) for n in
        ['calc_table_live_v2.py','cause_servo_socket_v3.py','cause_servo_interactive_v3.py','executor_v7.py','post_release_observation_v1.py',
         'input_state_table_v1.py','decision_receipt_v4.py','pointer_exchange_v1.py']}))
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
        report=run(query,batch,runtime,stage,spec['steps'],30000,save);save('report',report)
        data=(out/'report.json').read_bytes();review=receipt(data);states=table(data)
        save('receipt',review);save('state-table',states)
        result=dict(receipt=review,state_table=states,image=report.get('image'))
save('result',result);print(json.dumps(result))
