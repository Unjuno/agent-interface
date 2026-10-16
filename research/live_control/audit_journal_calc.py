"""Saved workbook, exact frames, declared evidence, and discoverable examples."""
import ast,hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v16 import Backend
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;root=HERE/'results/journal-calc-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(x) for x in (root/'delivered.jsonl').read_text().splitlines()]
flush=[json.loads(x) for x in (root/'delivery-flush.jsonl').read_text().splitlines()]
assert [r['delivery_id'] for r in delivered]==[r['delivery_id'] for r in flush]
decoder=Decoder('live-control');count=0
for row in events:
    if row['event']!='observation':continue
    count+=1;assert row['sequence']==count
    f=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(row['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
book=load_workbook(root/'sheet.xlsx');sheet=book.active
assert [sheet['A1'].value,sheet['A2'].value]==[532,590]
assert next(r for r in events if r['event']=='independent_evaluation')['success']
terminals=[r for r in events if r['event']=='terminal'];assert len(terminals)==2 and all(r['release']['verified'] and r['status']=='completed' for r in terminals)
assert not any(r['event']=='accepted' and r['id']=='enter_save' for r in events)
evidence=[r for r in delivered if r['event']=='decision_evidence']
by_id={r['delivery_id']:r for r in flush}
for row in evidence:
    obs=by_id[row['source_delivery_id']]['observation'];assert obs['sequence']==row['observation_sequence'] and obs['image']==row['image']
# Extract the actual ready examples rather than duplicating them in the test.
tree=ast.parse((HERE/'interactive_v18.py').read_text())
examples=next(ast.literal_eval(k.value) for node in ast.walk(tree) if isinstance(node,ast.Call) for k in node.keywords if k.arg=='basic_step_examples')
backend=Backend.__new__(Backend);backend.validate(examples)
try:backend.validate([{'op':'chord','keys':['Control_L','s']}])
except ValueError:pass
else:raise AssertionError('known incorrect chord accepted')
report=dict(exact_frames=count,delivery_pairs=len(flush),saved_values=[532,590],rejected_programs=1,
            accepted_programs=2,valid_ready_examples=examples,
            limitation='Workbook audit covers required cells only; full collateral and live v18 readiness untested')
(root/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
