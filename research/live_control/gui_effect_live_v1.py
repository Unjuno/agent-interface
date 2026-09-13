"""Explicit GUI readback decisions committed to runtime before independent scoring."""
import json
import sys
import uuid
from pathlib import Path
from pointer_exchange_v1 import run
from servo_review_v1 import build
from receipt_image import select_image
from report_pages_v2 import digest
from unix_json_deadline import exchange

HERE = Path(__file__).resolve().parent
stage, socket, directory = sys.argv[1:]
root=Path(directory); runtime=root/'runtime'; out=root/stage
assert stage in ('initial','servo','save','decide','recover','resave','decide_after','effect','finish')
out.mkdir(exist_ok=False)
def read(path):return json.loads((root/path).read_text())
def save(name,value):(out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def query(q):
    n=len(list(out.glob('query-*-request.json')))
    save(f'query-{n}-request',q)
    r=exchange(socket,q,timeout=16)
    save(f'query-{n}-reply',r)
    return r

if stage=='initial':
    names=['gui_effect_live_v1.py','effect_socket_v2.py','effect_interactive_v1.py','effect_fault_backend_v1.py',
           'effect_checkpoint_v1.py','effect_command_once_v1.py','cause_servo_session_v1.py',
           'session_v21.py','patch_servo_v5.py','pointer_exchange_v1.py','servo_review_v1.py','score_drag_v1.py']
    save('plan',dict(sources={n:digest((HERE/n).read_bytes()) for n in names}, seed=221,
                    task='20 screen px right at 118%, saved x66.95 +/-1, y/width/height50/40/30 +/-0.1',
                    allocation='one familiar replacement fixture; GUI geometry readback before oracle; no automatic retry',
                    decision_contract='Manual GUI decisions copied and their hash echoed by runtime clock before recovery/effect; no independent score read before decisions',
                    verified_model_id=None,model_tokens=None))
    result=query({'after':0,'events':['observation'],'timeout':5})
    save('batch',result)
    result={'batch':result,'image':select_image(result,runtime)}
elif stage in ('decide','decide_after'):
    previous='save' if stage=='decide' else 'resave'
    report=read(previous+'/report.json'); batch=report['last_reply']
    image=select_image(batch,runtime)
    path=root/('gui-decision.json' if stage=='decide' else 'gui-decision-after.json')
    data=path.read_bytes(); decision=json.loads(data)
    assert decision['image_sha256']==image['sha256']
    assert decision['evidence_kind']=='GUI screenshot only; independent score not requested'
    save('decision',decision)
    sha=digest(data)
    result=query({'after':batch['cursor'],'events':['clock'],'timeout':5,'request_id':uuid.uuid4().hex,
                  'command':{'op':'clock','gui_decision_sha256':sha}})
    assert result['status']=='boundary'
    assert any(e['event']=='command' and e['command'].get('gui_decision_sha256')==sha for e in result['records'])
    save('commit',dict(sha256=sha,decision_file=path.name,image=image,previous_report_sha256=digest((root/previous/'report.json').read_bytes())))
elif stage in ('servo','save','recover','resave'):
    if stage=='servo': batch=read('initial/batch.json')
    elif stage=='save':batch=read('servo/report.json')['last_reply']
    elif stage=='resave':batch=read('recover/report.json')['last_reply']
    else:
        batch=read('decide/result.json')
        previous=read('save/report.json')['last_reply']
        assert read('decide/query-0-request.json')['after']==previous['cursor']
        assert batch['cursor']==previous['cursor']+len(batch['records'])
        # Local concatenation of two contiguous received slices, not a new reply.
        batch=dict(batch,records=previous['records']+batch['records'])
        save('received-history',batch)
    source=select_image(batch,runtime)
    if stage=='servo':steps=[dict(op='pointer_servo',source_sequence=source['sequence'],box=[592,369,56,44],
                                target_delta=[20,0],points=[dict(x=618,y=391),dict(x=628,y=391)],duration_ms=100,max_corrections=3)]
    elif stage=='recover':
        decision=read('decide/decision.json')
        assert decision['action']=='set selected X field to 66.95'
        steps=[dict(op='pointer_click',x=560,y=106,button=1,duration_ms=80),
               dict(op='chord',modifier='Control_L',key='a'),dict(op='text',text='66.95'),
               dict(op='key',key='Return'),dict(op='settle',quiet_ms=80,timeout_ms=500)]
    else:steps=[dict(op='chord',modifier='Control_L',key='s'),dict(op='settle',quiet_ms=80,timeout_ms=500)]
    save('steps',steps)
    report=run(query,batch,runtime,stage,steps,30000,save)
    save('report',report)
    receipt=build((out/'report.json').read_bytes()); save('receipt',receipt)
    result={'receipt':receipt,'image':report.get('image')}
elif stage=='effect':
    committed=read('decide_after/commit.json')
    assert digest((root/committed['decision_file']).read_bytes())==committed['sha256']
    batch=read('decide_after/result.json')
    result=query({'after':batch['cursor'],'events':['saved_effect','rejected'],'timeout':5,'request_id':uuid.uuid4().hex,
                  'command':{'op':'effect','save_id':'resave'}})
else:
    batch=read('effect/result.json')
    result=query({'after':batch['cursor'],'events':['independent_evaluation'],'timeout':5,'request_id':uuid.uuid4().hex,'command':{'op':'finish'}})
save('result',result)
print(json.dumps(result))
