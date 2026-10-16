"""Changed-value GUI field task with full receipt plus nonempty state companion."""
import json
import sys
import uuid
from pathlib import Path
from pointer_exchange_v1 import run
from decision_receipt_v4 import build as receipt
from input_state_table_v1 import build as table
from receipt_image import select_image
from report_pages_v2 import digest
from unix_json_deadline import exchange

HERE=Path(__file__).resolve().parent
arm,stage,socket,directory=sys.argv[1:]
assert arm in ('A','B')
final_stage='save' if arm=='A' else 'bundle'
assert stage in ('initial','select','edit','save','bundle','decide','finish')
root=Path(directory);runtime=root/'runtime';out=root/stage;out.mkdir(exist_ok=False)
assert stage in (('initial','select','edit','save','decide','finish') if arm=='A' else ('initial','bundle','decide','finish'))
def read(path):return json.loads((root/path).read_text())
def save(name,value):(out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def query(q):
    n=len(list(out.glob('query-*-request.json')));save(f'query-{n}-request',q)
    r=exchange(socket,q,timeout=16);save(f'query-{n}-reply',r);return r
if stage=='initial':
    names=['bundle_pair_live_v1.py','input_state_table_v1.py','decision_receipt_v4.py','pointer_exchange_v1.py',
           'cause_servo_socket_v1.py','cause_servo_interactive_v1.py','cause_servo_session_v1.py']
    save('plan',dict(seed=223,arm=arm,sources={n:digest((HERE/n).read_bytes()) for n in names},
                    target=dict(x=69.5,y=50,width=40,height=30),absolute_tolerance=.01,
                    allocation='Registered AB pair, seed223 X69.5; one arm each, no reruns; same9steps separate vs bundled',
                    presentation='Full receipt plus state table instead of additional raw state extraction; empty table omitted',
                    decision='GUI screenshot judgment hashed into runtime clock before final independent evaluation',
                    verified_model_id=None,model_tokens=None))
    batch=query({'after':0,'events':['observation'],'timeout':5});save('batch',batch)
    result=dict(batch=batch,image=select_image(batch,runtime))
elif stage in ('select','edit','save','bundle'):
    previous={'select':'initial','edit':'select','save':'edit','bundle':'initial'}[stage]
    batch=read('initial/batch.json') if previous=='initial' else read(previous+'/report.json')['last_reply']
    select_steps=[dict(op='pointer_click',x=618,y=391,button=1,duration_ms=80),dict(op='settle',quiet_ms=80,timeout_ms=500)]
    edit_steps=[dict(op='pointer_click',x=560,y=106,button=1,duration_ms=80),dict(op='chord',modifier='Control_L',key='a'),dict(op='text',text='69.5'),dict(op='key',key='Return'),dict(op='settle',quiet_ms=80,timeout_ms=500)]
    save_steps=[dict(op='chord',modifier='Control_L',key='s'),dict(op='settle',quiet_ms=80,timeout_ms=500)]
    steps={'select':select_steps,'edit':edit_steps,'save':save_steps,'bundle':select_steps+edit_steps+save_steps}[stage]
    save('steps',steps);report=run(query,batch,runtime,stage,steps,30000,save);save('report',report)
    data=(out/'report.json').read_bytes();review=receipt(data);save('receipt',review)
    states=table(data)
    result=dict(receipt=review,image=report.get('image'))
    if states['table']['observations']:
        save('state-table',states);result['state_table']=states
elif stage=='decide':
    data=(root/'gui-decision.json').read_bytes();decision=json.loads(data)
    report=read(final_stage+'/report.json');image=select_image(report['last_reply'],runtime)
    assert decision['image_sha256']==image['sha256']
    assert decision['evidence_kind']=='GUI screenshot only; independent score not requested'
    save('decision',decision);sha=digest(data)
    result=query({'after':report['last_reply']['cursor'],'events':['clock'],'timeout':5,'request_id':uuid.uuid4().hex,
                  'command':{'op':'clock','gui_decision_sha256':sha}})
    assert any(e['event']=='command' and e['command'].get('gui_decision_sha256')==sha for e in result['records'])
    save('commit',dict(sha256=sha,image=image,report_sha256=digest((root/final_stage/'report.json').read_bytes())))
else:
    assert digest((root/'gui-decision.json').read_bytes())==read('decide/commit.json')['sha256']
    result=query({'after':read('decide/result.json')['cursor'],'events':['independent_evaluation'],'timeout':5,
                  'request_id':uuid.uuid4().hex,'command':{'op':'finish'}})
save('result',result);print(json.dumps(result))
