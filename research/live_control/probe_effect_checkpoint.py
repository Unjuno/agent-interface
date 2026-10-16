"""Open-window missing/mismatch/error, immutable requests and busy/closed controls."""
import hashlib,json,tempfile,threading,time
from pathlib import Path
from effect_checkpoint import sample,Checkpoints
HERE=Path(__file__).resolve().parent;out=HERE/'results/effect-checkpoint-01';out.mkdir(exist_ok=False)
with tempfile.TemporaryDirectory() as temporary:
    path=Path(temporary)/'saved.txt';contract=dict(kind='saved_form_value',expected='right')
    missing=sample(path,contract);assert missing['status']=='UNKNOWN'
    path.write_text('value=wrong');wrong=sample(path,contract);assert wrong['status']=='UNKNOWN'
    path.write_text('value=right');match=sample(path,contract);assert match['status']=='VERIFIED' and match['task_success'] is None
    path.write_bytes(b'\xff');broken=sample(path,contract);assert broken['status']=='UNKNOWN'
    path.write_bytes(b'x'*65537);large=sample(path,contract);assert large['status']=='UNKNOWN'
    records=[];arrived=threading.Event();entered=threading.Event();release=threading.Event()
    def emit(record):records.append(record);arrived.set()
    def blocked(path,c):
        entered.set();assert release.wait(2);return dict(status='UNKNOWN',contract=c)
    service=Checkpoints(emit);metadata=dict(transport_request_id='first')
    service.request(path,contract,metadata,blocked);assert entered.wait(1)
    contract['expected']='changed';metadata['transport_request_id']='changed'
    service.request(path,contract,dict(transport_request_id='second'),blocked)
    assert records[0]['reason']=='verifier_busy' and records[0]['transport_request_id']=='second'
    arrived.clear();release.set();assert arrived.wait(1)
    assert records[1]['transport_request_id']=='first' and records[1]['evidence']['contract']['expected']=='right'
    service.close()
    try:service.request(path,contract,{})
    except ValueError:pass
    else:raise AssertionError('closed service accepted')
    failed=[];done=threading.Event()
    def failure(path,c):raise RuntimeError('injected')
    other=Checkpoints(lambda r:(failed.append(r),done.set()))
    other.request(path,contract,dict(transport_request_id='failure'),failure)
    assert done.wait(1) and failed[0]['evidence']['status']=='UNKNOWN';other.close()
result=dict(missing=missing,mismatch=wrong,match=match,malformed=broken,oversized=large,
    busy_and_copy_records=records,verifier_exception=failed,closed_request_rejected=True,
    scope='artifact and worker controls; not wall-time or cancellation deadline proof')
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'effect_checkpoint.py',HERE/'saved_effect.py')},indent=2)+'\n')
print('missing/mismatch/malformed/oversize UNKNOWN; match scoped VERIFIED; busy/copy/closed/exception controls passed')
