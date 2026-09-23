"""Audit real cancellation timing, owner release and retry command counts."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;report=[]
for cohort in ('socket-cancel-delay-01','socket-cancel-delay-03'):
    root=HERE/'results'/cohort;d=root/'runtime'
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for name,h in json.loads((d/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()]
    responses=json.loads((root/'responses.json').read_text())
    blocker=next(r for r in responses if r['request'].get('request_id')=='blocker')
    cancel=next(r for r in responses if r['request'].get('request_id')=='cancel')
    terminal=next(r for r in events if r['event']=='terminal' and r['id']=='hold')
    assert terminal['status']=='cancelled' and terminal['release']['verified']
    admissions=[r for r in events if r['event']=='input_admission']
    assert admissions,'actual key admission required'
    assert admissions[0]['input_ack_ns']<terminal['release']['verified_ns']
    release_before_wait=terminal['release']['verified_ns']<blocker['reply']['returned_ns']
    assert release_before_wait==(cohort.endswith('03'))
    assert sum(r['event']=='clock' for r in events)==3
    retry=next(r for r in responses if r['request'].get('request_id')=='dropped')
    assert retry['reply']['command_receipt']['replayed']
    decoder=Decoder('live-control');count=0
    for event in events:
        if event['event']!='observation':continue
        count+=1;f=decoder.accept((d/f'{count:03d}.ait').read_bytes())
        with Image.open(d/Path(event['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
    report.append(dict(cohort=cohort,frames=count,key_admission_recorded=True,release_before_long_read_end=release_before_wait,
                       cancel_send_to_verified_release_ms=(terminal['release']['verified_ns']-cancel['started_ns'])/1e6))
(HERE/'results/socket-cancel-delay-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
