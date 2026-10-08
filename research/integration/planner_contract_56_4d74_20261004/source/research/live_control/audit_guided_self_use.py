"""Audit actual assistant pilot; timeout is evidence, not success."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
rows=[]
for n in (1,2):
    root=HERE/f'results/guided-self-use-{n:02d}'
    for name,digest in json.loads((root/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==digest,name
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');count=0
    for event in events:
        if event['event']!='observation':continue
        count+=1;assert event['sequence']==count
        frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
        with Image.open(root/Path(event['image']).name) as im:
            assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
    row={'cohort':n,'exact_frames':count}
    if n==2:
        offered=next(e for e in events if e['event']=='pointer_yield')
        reply=next(e for e in events if e['event']=='command' and e['command']['op']=='pointer_reply')
        terminal=next(e for e in events if e['event']=='terminal' and e['id']=='visual2')
        evaluation=next(e for e in events if e['event']=='independent_evaluation')
        assert terminal['status']=='needs_decision' and terminal['release']['verified']
        assert reply['received_ns']>offered['reply_until_ns']
        assert not any(e['event']=='reply_accepted' for e in events)
        assert evaluation['success'] is False
        row.update(reply_after_yield_ms=(reply['received_ns']-offered['emit_started_ns'])/1e6,
                   reply_lateness_ms=(reply['received_ns']-offered['reply_until_ns'])/1e6,
                   terminal=terminal,evaluation=evaluation,
                   rejections=[e['reason'] for e in events if e['event']=='rejected'])
    rows.append(row)
(HERE/'results/guided-self-use-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
