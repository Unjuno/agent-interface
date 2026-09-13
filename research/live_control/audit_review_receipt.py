"""Receipt source preservation and actual assistant xterm evidence."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from presentation_v2 import Presentation
HERE=Path(__file__).resolve().parent;root=HERE/'results/review-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(x) for x in (root/'delivered.jsonl').read_text().splitlines()]
decoder=Decoder('live-control');count=0
for r in events:
    if r['event']!='observation':continue
    count+=1;f=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
terminal=next(r for r in delivered if r['event']=='terminal');assert terminal['release']['verified']
assert terminal['review']['observation']['sequence']==6 and Path(terminal['review']['observation']['image']).name=='003.png'
assert all('review' not in r for r in events)
evaluation=next(r for r in events if r['event']=='independent_evaluation');assert evaluation['success'] and evaluation['actual']=='t991018'
# Prior-program and absent observations must not masquerade as new captures.
p=Presentation();p.project(dict(event='observation',id='old',step=0,sequence=4,capture_ns=2,image='old.png',image_reused=True))
r=p.project(dict(event='terminal',id='new',terminal_ns=3))[-1]
assert r['review']['observation']['from_this_program'] is False
p=Presentation();assert p.project(dict(event='terminal',id='empty',terminal_ns=1))[-1]['review']['observation'] is None
report=dict(exact_frames=count,latest_sequence=6,image='003.png',success=True,prior_and_missing_observation_checks=True,
            claim_scope='presentation usability; no matched latency/token improvement measured')
(HERE/'results/review-receipt-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
