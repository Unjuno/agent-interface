"""Frame/prefix verification and reject an unqualified cross-process interval."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;out=HERE/'results/checkpoint-cancel-01';root=out/'runtime'
responses=json.loads((out/'responses.json').read_text())
delivered=[json.loads(s) for s in (root/'delivered.jsonl').read_text().splitlines()]
records=[]
for response in responses:
    assert response['request']['after']==len(records)
    records+=response['reply']['records']
    assert response['reply']['cursor']==len(records)
assert records==delivered[:len(records)]
for name,h in json.loads((root/'sources.json').read_text()).items():
    assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
decoder=Decoder('live-control');frames=0
for event in events:
    if event['event']!='observation':continue
    frames+=1;frame=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:
        assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
cancel=next(r for r in responses if r['cancel_lane'])
terminal_index=next(i for i,r in enumerate(responses) if r['request']['events']==['terminal'])
query_index=next(i for i,r in enumerate(responses) if r['request'].get('read_request_id')=='blocked-query' and 'command' not in r['request'])
assert terminal_index<query_index
result=dict(exact_frames=frames,retained_prefix_records=len(records),runtime_source_hashes_verified=True,
    cancel_roundtrip_ms=(cancel['finished_ns']-cancel['started_ns'])/1e6,
    cross_process_cancel_to_terminal_ns=None,
    cross_process_missingness='probe did not record its parent clock descriptor; raw computed interval is not accepted as domain-verified',
    cancellation_before_gate_release='proven by sequential probe control flow and received terminal, not cross-domain timestamp subtraction')
(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'audit-source.json').write_text(json.dumps({Path(__file__).name:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(result,indent=2))
