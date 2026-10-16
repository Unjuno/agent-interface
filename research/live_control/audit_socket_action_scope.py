"""Audit retained runtime frames, expiry/release and transport source hashes."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;rows=[]
for cohort in ('socket-action-scope-01',):
    root=HERE/'results'/cohort;d=root/'runtime'
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for name,h in json.loads((d/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');count=0
    for event in events:
        if event['event']!='observation':continue
        count+=1;f=decoder.accept((d/f'{count:03d}.ait').read_bytes())
        with Image.open(d/Path(event['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
    terminal=next(e for e in events if e['event']=='terminal');assert terminal['release']['verified']
    assert terminal['status']==('expired' if cohort.startswith('live-pipe') else 'cancelled')
    owner=json.loads((d/'owner-events.json').read_text());assert owner[-1]['reason']=='close' and owner[-1]['verified']
    rows.append(dict(cohort=cohort,exact_frames=count,terminal=terminal['status'],owner_close_verified=True))
(HERE/'results/socket-action-scope-audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))

(HERE/'results/socket-action-scope-01/scope-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'event_scope.py',HERE/'event_cursor_v2.py',HERE/'event_socket_v7.py')},indent=2)+'\n')
