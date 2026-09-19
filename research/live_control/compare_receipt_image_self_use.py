"""Compare known sequential self-use and verify receipt-selected image references."""
import hashlib,json
from pathlib import Path
from receipt_image import select_image
HERE=Path(__file__).resolve().parent
rows=[]
for cohort in ('receipt-clock-self-use-01','receipt-image-self-use-01'):
    root=HERE/'results'/cohort
    events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    accepted=[r for r in events if r['event']=='accepted']
    initial=json.loads((root/'read-initial.json').read_text())
    modal=json.loads((root/'read-modal.json').read_text())
    rows.append(dict(cohort=cohort,
        initial_socket_return_to_accept_ms=(accepted[0]['accepted_ns']-initial['returned_ns'])/1e6,
        modal_socket_return_to_accept_ms=(accepted[1]['accepted_ns']-modal['returned_ns'])/1e6,
        selected_images={name:select_image(json.loads((root/f'read-{name}.json').read_text()),root) for name in ('initial','modal')},
        scope='socket return to admission includes model, orchestration, transport and runtime; not model-only time'))
for name in ('enter','confirm'):
    before=json.loads((HERE/'results/receipt-clock-self-use-01'/f'{name}.json').read_text())
    after=json.loads((HERE/'results/receipt-image-self-use-01'/f'{name}.json').read_text())
    assert before['steps']==after['steps']
    assert before['expected_sequence']==after['expected_sequence']
    assert before['decision_evidence']==after['decision_evidence']
out=HERE/'results/receipt-image-self-use-comparison.json'
out.write_text(json.dumps(dict(runs=rows,source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'receipt_image.py',HERE/'audit_receipt_image_self_use.py')}),indent=2)+'\n')
print(json.dumps(rows,indent=2))
