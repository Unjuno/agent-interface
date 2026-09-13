"""Actual Calc checkpoint use: scoped open-window evidence and final saved output."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
from timing_clock import interval
HERE=Path(__file__).resolve().parent;root=HERE/'results/checkpoint-calc-self-use-01'
read=lambda name:json.loads((root/name).read_text())
events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(s) for s in (root/'delivered.jsonl').read_text().splitlines()]
initial=read('read-initial.json');entry=read('enter/report.json');confirm=read('confirm/report.json')
before=read('before-checkpoint.json');after=read('after-checkpoint.json');finish=read('finish.json')
clock=read('timing-clock.json');assert clock['status']=='identified'
assert entry['clock']==confirm['clock']==before['clock']==after['clock']==finish['clock']==clock
assert all(r['clock_domain_id']==clock['domain_id'] for r in events)
assert 'outcome' not in entry and 'outcome' not in confirm
pre=before['reply']['records'][-1];post=after['reply']['records'][-1]
assert pre['transport_request_id']=='check-before-confirm' and post['transport_request_id']=='check-after-confirm'
assert pre['evidence']['status']=='UNKNOWN' and pre['evidence']['actual']==dict(A1=None,A2=None)
assert post['evidence']['status']=='VERIFIED' and post['evidence']['actual']==dict(A1=612,A2=129)
assert pre['task_success'] is post['task_success'] is None
assert pre['evidence']['observation_closed'] is post['evidence']['observation_closed'] is False
assert not any(r['event']=='independent_evaluation' for r in delivered[:after['reply']['cursor']])
score=finish['reply']['records'][-1];assert score['success'] is True and score['actual']==[612,129]
assert 'admitted_request' not in score  # legacy explicit finish, no fabricated action attribution
assert hashlib.sha256((root/'sheet.xlsx').read_bytes()).hexdigest()==post['evidence']['artifact_sha256']
wb=load_workbook(root/'sheet.xlsx');assert [wb.active['A1'].value,wb.active['A2'].value]==[612,129];wb.close()
prefix=initial['records']+entry['records']+before['reply']['records']+confirm['records']+after['reply']['records']+finish['reply']['records']
assert prefix==delivered[:finish['reply']['cursor']]
accepted=[r for r in events if r['event']=='accepted'];terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2 and not any(r['event']=='rejected' for r in events)
assert all(r['status']=='completed' and r['release']['verified'] for r in terminals)
assert all(a['admitted_request']==t['admitted_request'] for a,t in zip(accepted,terminals))
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
decoder=Decoder('live-control');frames=0
for event in events:
    if event['event']!='observation':continue
    frames+=1;frame=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:
        assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
for name,h in read('sources.json').items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
def duration(a,b):
    value=interval(a,clock,b,clock);assert value['status']=='comparable';return value['duration_ns']/1e6
result=dict(before='UNKNOWN',after='VERIFIED',checkpoint_task_success=None,final_success=True,
    exact_frames=frames,admitted_programs=2,socket_calls_including_finish=6,retained_prefix_records=len(prefix),
    query_roundtrip_ms=[duration(q['started_ns'],q['returned_ns']) for q in (before,after)],
    sample_ms=[duration(q['evidence']['started_ns'],q['evidence']['finished_ns']) for q in (pre,post)],
    before_query_return_to_confirm_main_ms=duration(before['returned_ns'],read('confirm/client-endpoints.json')['endpoints']['client_main_entered_ns']),
    after_query_return_to_finish_start_ms=duration(after['returned_ns'],finish['started_ns']),
    initial_capture_to_verified_query_return_ms=duration(initial['records'][1]['capture_ns'],after['returned_ns']),
    initial_capture_to_final_score_return_ms=duration(initial['records'][1]['capture_ns'],finish['returned_ns']),
    limitation='Actual assistant known Calc modal; no model receipt/token measurement or matched speedup. Pre-save artifact bytes not archived separately.')
(root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
files=[Path(__file__),HERE/'effect_checkpoint.py',HERE/'saved_effect.py',HERE/'prepared_exchange_v6.py',HERE/'prepare_program.py',HERE/'receipt_image.py',HERE/'timing_clock.py',HERE/'event_socket_v14.py',HERE/'event_cursor_v6.py',HERE/'request_boundary_v3.py',HERE/'command_once_v3.py']
(root/'client-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print(json.dumps(result,indent=2))
