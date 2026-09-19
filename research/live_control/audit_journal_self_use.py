"""Audit actual delivery cohorts and the source-reference collision regression."""
import copy
import hashlib
import json
import statistics
import time
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from delivery_ledger_v2 import DeliveryLedger

HERE=Path(__file__).resolve().parent
reports=[]
for n in (2,):
    root=HERE/'results/journal-self-use-01'
    for name,digest in json.loads((root/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==digest,name
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    delivered=[json.loads(x) for x in (root/'delivered.jsonl').read_text().splitlines()]
    flushed=[json.loads(x) for x in (root/'delivery-flush.jsonl').read_text().splitlines()]
    assert [r['delivery_id'] for r in delivered]==[r['delivery_id'] for r in flushed]
    assert len({r['delivery_id'] for r in delivered})==len(delivered)
    for item,receipt in zip(delivered,flushed):
        assert receipt['flushed_ns']>=receipt['started_ns']
        assert receipt['utf8_bytes']==len((json.dumps(item)+'\n').encode())
    evidence=next(r for r in events if r['event']=='decision_evidence')
    visible=next(r for r in delivered if r['event']=='decision_evidence')
    if n==1:
        assert visible['delivery_id']!=evidence['delivery_id'] # Retained v1 bug.
    else:
        assert visible['source_delivery_id']==evidence['source_delivery_id']=='delivery:2'
        assert visible['source_delivery_id']!=visible['delivery_id']
    observations=[r for r in events if r['event']=='observation']
    decoder=Decoder('live-control')
    for row in observations:
        frame=decoder.accept((root/f"{row['sequence']:03d}.ait").read_bytes())
        with Image.open(root/Path(row['image']).name) as im:
            assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
    evaluation=next(r for r in events if r['event']=='independent_evaluation')
    assert evaluation['success'] and (root/'submitted.txt').read_text().strip()==evaluation['actual']
    terminal=next(r for r in events if r['event']=='terminal')
    accepted=next(r for r in events if r['event']=='accepted')
    assert terminal['release']['verified']
    elapsed=[(r['flushed_ns']-r['started_ns'])/1e6 for r in flushed]
    reports.append(dict(cohort='journal-self-use-01',exact_frames=len(observations),delivery_count=len(delivered),
                        flush_median_ms=statistics.median(elapsed),flush_max_ms=max(elapsed),
                        receipt_file_bytes=(root/'delivery-flush.jsonl').stat().st_size,
                        local_program_ms=(terminal['terminal_ns']-accepted['accepted_ns'])/1e6,
                        reference_collision_retained=(n==1),success=True))

(HERE/'results/journal-self-use-01/audit.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))

