"""Audit actual assistant-controlled Calc episode; do not infer model receipt time."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;root=HERE/'results/receipt-clock-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(x) for x in (root/'delivered.jsonl').read_text().splitlines()]
receipts={r['delivery_id'] for r in map(json.loads,(root/'delivery-flush.jsonl').read_text().splitlines())}
early,=[r for r in delivered if r['event']=='effect_evidence'];evaluation,=[r for r in delivered if r['event']=='independent_evaluation']
assert early['delivery_id'] in receipts and evaluation['delivery_id'] in receipts
assert early['effect']==evaluation['effect'] and early['effect']['status']=='VERIFIED' and evaluation['success']
wb=load_workbook(root/'sheet.xlsx');values=[wb.active['A1'].value,wb.active['A2'].value];wb.close();assert values==[532,590]
assert hashlib.sha256((root/'sheet.xlsx').read_bytes()).hexdigest()==early['effect']['artifact_sha256']
state=json.loads((root/'finalization-status.json').read_text());assert state['admission_closed'] and state['effect_output_flushed'] and state['output_flushed']
assert state['effect']==early['effect']
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
accepted=[r for r in events if r['event']=='accepted'];terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2 and all(r['status']=='completed' and r['release']['verified'] for r in terminals)
assert not any(r['event']=='rejected' for r in events)
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
batches=[json.loads((root/('read-'+name+'.json')).read_text()) for name in ('initial','modal','effect','final')]
assert [r for b in batches for r in b['records']]==delivered[:23]
assert batches[-2]['records'][-1]['event']=='effect_evidence' and len(batches[-1]['records'])==1
assert not any(r['event']=='independent_evaluation' for r in batches[-2]['records'])
assert batches[-1]['command_receipt']['replayed']
assert len([r for r in events if r['event']=='command' and r['command'].get('id')=='confirm_excel'])==1
lineage=early['admitted_request']
assert lineage==evaluation['admitted_request']==terminals[-1]['admitted_request']
assert lineage['transport_request_id']=='confirm' and lineage['declared_action_id']=='confirm_excel'
confirmation=next(r['command'] for r in events if r['event']=='command' and r['command'].get('id')=='confirm_excel')
assert confirmation['valid_until_ns']==terminals[0]['terminal_ns']+30_000_000_000
assert accepted[1]['accepted_ns']<confirmation['valid_until_ns']
initial=next(r for r in events if r['event']=='observation')
report=dict(saved_values=values,exact_frames=count,accepted_programs=2,rejections=0,
            clock_requests=sum(r['event']=='clock' for r in events),
            first_capture_to_effect_emit_ms=(early['emit_started_ns']-initial['capture_ns'])/1e6,
            modal_terminal_to_confirm_accept_ms=(accepted[1]['accepted_ns']-terminals[0]['terminal_ns'])/1e6,
            final_terminal_to_effect_emit_ms=(early['emit_started_ns']-terminals[1]['terminal_ns'])/1e6,
            final_terminal_to_evaluation_emit_ms=(evaluation['emit_started_ns']-terminals[1]['terminal_ns'])/1e6,
            local_program_ms=[(t['terminal_ns']-a['accepted_ns'])/1e6 for a,t in zip(accepted,terminals)],
            effect_emit_to_socket_return_ms=(batches[-2]['returned_ns']-early['emit_started_ns'])/1e6,
            first_capture_to_effect_socket_return_ms=(batches[-2]['returned_ns']-initial['capture_ns'])/1e6,
            socket_reads_before_cleanup=len(batches),
            early_socket_return_before_final_emit=batches[-2]['returned_ns']<evaluation['emit_started_ns'],model_receipt_timestamps=None,
            limitation='actual assistant input with known task; combined send/wait; familiar sequential run, no matched causal speedup; no matched A/B or model token measurement')
(HERE/'results/receipt-clock-self-use-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

(root/'transport-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'event_socket_v10.py',HERE/'event_cursor_v4.py',HERE/'request_boundary.py',HERE/'admitted_lineage.py')},indent=2)+'\n')
