"""Audit actual visual confirmation and an unplanned expired-request recovery."""
import hashlib,json,urllib.parse
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
root=HERE/'results/confirmation-self-use-01'
read=lambda p:json.loads((root/p).read_text())
events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(s) for s in (root/'delivered.jsonl').read_text().splitlines()]
reports={name:read(f'{name}/report.json') for name in ('navigate','attempt','retry','confirm')}
assert reports['attempt']['status']=='request_rejected'
rejections=[r for r in events if r['event']=='rejected']
assert len(rejections)==1 and rejections[0]['reason']=='intent validity expired'
assert rejections[0]['declared_action_id']=='attempt'
assert not any(r.get('id')=='attempt' and r['event'] in ('accepted','observation','terminal') for r in events)
accepted=[r for r in events if r['event']=='accepted']
terminals=[r for r in events if r['event']=='terminal']
assert [r['id'] for r in accepted]==['navigate','attempt_after_expiry','confirm_replace']
assert len(terminals)==3 and all(r['status']=='completed' and r['release']['verified'] for r in terminals)
assert 'outcome' not in reports['retry']
score=reports['confirm']['outcome']['evidence']
assert reports['confirm']['outcome']['task_success'] is True
assert urllib.parse.parse_qs((root/'submitted.txt').read_text())==score['actual']=={'value':['t991029']}
assert score['admitted_request']==accepted[-1]['admitted_request']==terminals[-1]['admitted_request']
assert len([r for r in events if r['event']=='independent_evaluation'])==1
assert reports['confirm']['drain']['attempted'] is False
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
prefix=read('read-initial.json')['records']+reports['navigate']['records']+reports['attempt']['records']
prefix+=read('refresh-clock.json')['records']+reports['retry']['records']+reports['confirm']['records']
assert prefix==delivered[:reports['confirm']['cursor']]
clock=read('timing-clock.json')
assert clock['status']=='identified' and all(r['clock_domain_id']==clock['domain_id'] for r in events)
marks={}
for name,report in reports.items():
    sidecar=read(f'{name}/client-endpoints.json')
    assert sidecar['clock']==report['clock']==clock
    marks[name]=sidecar['endpoints']
    assert list(marks[name].values())==sorted(marks[name].values())
    assert all(v is None for v in sidecar['unobserved_endpoints'].values())
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:
        assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
for name,h in read('sources.json').items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
assert not (root/'submission-attempts.jsonl').exists()
result=dict(exact_frames=count,accepted_programs=3,rejected_programs=1,task_success=True,
    delivered_prefix_records=len(prefix),socket_calls_before_cleanup=6,
    form_flush_to_expired_client_main_ms=(marks['attempt']['client_main_entered_ns']-marks['navigate']['stdout_flush_returned_ns'])/1e6,
    rejected_flush_to_retry_main_ms=(marks['retry']['client_main_entered_ns']-marks['attempt']['stdout_flush_returned_ns'])/1e6,
    confirmation_page_flush_to_next_main_ms=(marks['confirm']['client_main_entered_ns']-marks['retry']['stdout_flush_returned_ns'])/1e6,
    first_capture_to_final_flush_ms=(marks['confirm']['stdout_flush_returned_ns']-next(r['capture_ns'] for r in events if r['event']=='observation'))/1e6,
    missing_http_attempt_archive=True,
    limitation='Known designed confirmation fixture; actual unplanned lease expiry. No retained HTTP attempt log, model timestamps, token counts or matched speedup.')
(root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
sources=[Path(__file__),HERE/'confirmation_browser_entry.py',HERE/'confirmation_socket_entry.py',HERE/'prepared_exchange_v6.py',HERE/'prepare_program.py',HERE/'receipt_image.py',HERE/'timing_clock.py']
(root/'client-fixture-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print(json.dumps(result,indent=2))
