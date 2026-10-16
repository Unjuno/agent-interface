"""Audit branching actual Calc use with explicit endpoint missingness."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
from prepare_program import prepare
HERE=Path(__file__).resolve().parent;root=HERE/'results/prepared-calc-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
initial=json.loads((root/'read-initial.json').read_text())
enter=json.loads((root/'enter/report.json').read_text());confirm=json.loads((root/'confirm/report.json').read_text())
final=json.loads((root/'outcome.json').read_text());score=final['result']['evidence']
early=confirm['outcome']['evidence']
assert confirm['outcome']['task_success'] is None and confirm['outcome']['effect_status']=='VERIFIED'
assert final['result']['task_success'] is True and early['effect']==score['effect']
wb=load_workbook(root/'sheet.xlsx');assert [wb.active['A1'].value,wb.active['A2'].value]==[612,129];wb.close()
assert hashlib.sha256((root/'sheet.xlsx').read_bytes()).hexdigest()==early['effect']['artifact_sha256']
accepted=[r for r in events if r['event']=='accepted'];terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2 and all(t['status']=='completed' and t['release']['verified'] for t in terminals)
assert not any(r['event']=='rejected' for r in events)
assert accepted[-1]['admitted_request']==terminals[-1]['admitted_request']==early['admitted_request']==score['admitted_request']
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
enter_reply=json.loads((root/'enter/reply.json').read_text());confirm_reply=json.loads((root/'confirm/reply.json').read_text())
assert initial['records']+enter_reply['records']+confirm_reply['records']+final['transcript'][0]['reply']['records']==delivered[:23]
for name,source,program,finished in (('enter',initial,'enter_save',False),('confirm',enter_reply,'confirm_excel',True)):
    prepared=json.loads((root/name/'preparation.json').read_text())
    assert prepare(source,root,program,json.loads((root/f'{name}-steps.json').read_text()),lease_ms=30000,finish_after=finished)==prepared
    assert json.loads((root/name/'request.json').read_text())['command']==prepared['command']
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
first=next(r for r in events if r['event']=='observation')
report=dict(actual=[612,129],exact_frames=count,programs=2,socket_calls_before_cleanup=4,
    first_capture_to_early_socket_return_ms=(confirm['returned_ns']-first['capture_ns'])/1e6,
    first_capture_to_final_client_return_ms=(final['client_returned_ns']-first['capture_ns'])/1e6,
    modal_socket_return_to_confirmation_admission_ms=(accepted[-1]['accepted_ns']-enter['returned_ns'])/1e6,
    early_socket_return_to_final_client_start_ms=(final['client_started_ns']-confirm['returned_ns'])/1e6,
    early_emit_to_final_emit_ms=(score['emit_started_ns']-early['emit_started_ns'])/1e6,
    final_emit_to_final_client_start_ms=(final['client_started_ns']-score['emit_started_ns'])/1e6,
    local_program_ms=[(t['terminal_ns']-a['accepted_ns'])/1e6 for a,t in zip(accepted,terminals)],
    missing_endpoints=dict(model_image_receipt='NOT_RECORDED',model_generation_start='NOT_RECORDED',model_generation_end='NOT_RECORDED',model_final_receipt='NOT_RECORDED'),
    limitation='same local Linux perf_counter domain assumed for this session; no exported clock epoch/uncertainty envelope, no model timing attribution or matched speedup')
(HERE/'results/prepared-calc-self-use-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'client-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'prepared_exchange.py',HERE/'prepare_program.py',HERE/'receipt_image.py',HERE/'outcome_wait.py',HERE/'outcome_client.py',HERE/'outcome_fallback_v2.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(report,indent=2))
