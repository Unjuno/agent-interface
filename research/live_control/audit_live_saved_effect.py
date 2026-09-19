"""Audit live output/retention and callback-level unknown/failure semantics."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from finalization_v2 import finalize
HERE=Path(__file__).resolve().parent;root=HERE/'results/live-saved-effect-02';report=[]
for case in ('save','unsaved'):
    d=root/case
    for name,h in json.loads((d/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h,name
    state=json.loads((d/'finalization-status.json').read_text());assert state['admission_closed'] and state['output_flushed']
    events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()]
    terminal=next(e for e in events if e['event']=='terminal' and e['id']=='final')
    effect=state['effect'];assert terminal['terminal_ns']<=state['started_ns']<=effect['started_ns']<=effect['finished_ns']
    delivered=[json.loads(x) for x in (d/'supervisor-visible.jsonl').read_text().splitlines()]
    evaluation,=[e for e in delivered if e['event']=='independent_evaluation']
    assert evaluation['effect']==effect
    receipts={e['delivery_id'] for e in map(json.loads,(d/'delivery-flush.jsonl').read_text().splitlines())}
    assert evaluation['delivery_id'] in receipts
    decoder=Decoder('live-control');count=0
    for event in events:
        if event['event']!='observation':continue
        count+=1;f=decoder.accept((d/f'{count:03d}.ait').read_bytes())
        with Image.open(d/Path(event['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
    report.append(dict(case=case,frames=count,effect=effect['status'],confirmed_output=True))
for fault in ('none','evaluate','publish'):
    trace=[]
    def close():trace.append('closed')
    def observe():trace.append('effect');return dict(status='UNKNOWN',reason='evidence_unavailable')
    def evaluate():
        trace.append('evaluate')
        if fault=='evaluate':raise OSError('injected scorer failure')
        return dict(success=False)
    def publish(record):
        trace.append('publish');assert record['effect']['status']=='UNKNOWN'
        return fault!='publish'
    result=finalize('test',close,evaluate,publish,observe)
    assert result['effect']['status']=='UNKNOWN' and result['admission_closed']
    assert result['status']==('finished' if fault=='none' else 'finalization_error')
    assert trace[:3]==['closed','effect','evaluate']
    report.append(dict(callback_fault=fault,result=result))
(HERE/'results/live-saved-effect-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
