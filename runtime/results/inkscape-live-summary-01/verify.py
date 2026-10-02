"""Verify retained four-case control equivalence and critical feedback, read-only."""
from pathlib import Path
import json,subprocess,sys
from runtime.cli_v1.review import review_bytes
root=Path(__file__).resolve().parent
schedule=json.loads((root/'schedule.json').read_text())
for row in schedule:
    case=root/row['case']
    subprocess.run([sys.executable,str(root/'verify_case.py'),row['case']],check=True)
    for index in (2,3):
        raw=(case/'public'/f'{index:03d}-raw.json').read_bytes()
        full=review_bytes(raw,case/'public',compact=True,report_refs=True)
        shown=json.loads((case/'replies'/f'{index:03d}.json').read_text())['reply']
        if any(full.get(k)!=shown.get(k) for k in ('image','image_reference','outcome_summary')):raise ValueError('critical feedback mismatch')
        expected='agent-interface/receipt-view-dispatch-summary-v1' if row['detail']=='summary' else 'agent-interface/receipt-view-v3-report-ref'
        if shown['receipt']['schema']!=expected:raise ValueError('detail treatment not delivered')
for pair in (1,2):
    a=root/f'pair{pair}-full';b=root/f'pair{pair}-summary'
    if (a/'two-rectangles.svg').read_bytes()!=(b/'two-rectangles.svg').read_bytes():raise ValueError('saved task differs within pair')
    for index in (2,3):
        requests=[json.loads((c/'commands'/f'{index:03d}.json').read_text())['program'] for c in (a,b)]
        for program in requests:program['authority'].pop('expires_at_ns')
        if requests[0]!=requests[1]:raise ValueError('program semantics differ')
print(json.dumps({'status':'PASS','cases':4,'input_programs':8,'commands':16,'primary_images':12,'paired_programs_and_saved_svg_match':True,'scope':'retained control/byte/task checks, not latency/usage causality or primary perception proof'}))
