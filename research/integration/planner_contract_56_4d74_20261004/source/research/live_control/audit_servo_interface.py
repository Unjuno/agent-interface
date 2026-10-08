"""Verify planner-facing servo evidence without treating local goal as task score."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
rows=[]
for name in ('servo-self-use-01','servo-outcome-01/0','servo-outcome-01/40'):
    out=HERE/'results'/name
    manifest=out/'sources.json' if name=='servo-self-use-01' else out.parent/'sources.json'
    base=HERE.parent if name=='servo-self-use-01' else HERE
    for source,digest in json.loads(manifest.read_text()).items():assert hashlib.sha256((base/source).read_bytes()).hexdigest()==digest
    events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');count=0
    for r in events:
        if r['event']!='observation':continue
        count+=1;assert r['sequence']==count
        f=decoder.accept((out/f'{count:03d}.ait').read_bytes())
        with Image.open(out/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
    terminals=[r for r in events if r['event']=='terminal'];assert all(r['release']['verified'] for r in terminals)
    terminal=next(r for r in terminals if r['id']=='servo')
    outcome=next(r for r in events if r['event']=='servo_outcome')
    lost=name.endswith('/40')
    assert terminal['status']==('needs_decision' if lost else 'completed')
    assert outcome['reason']==('lost' if lost else 'local_goal_reached')
    assert outcome['semantic_effect_verified'] is False
    row={'trial':name,'exact_frames':count,'terminal':terminal['status'],'outcome':outcome['reason']}
    if name=='servo-self-use-01':
        actual=next(r for r in events if r['event']=='independent_evaluation')
        rect=ET.parse(out/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
        assert all(rect.get(k)==v for k,v in actual['actual'].items())
        dx=(float(rect.get('x'))-50)*1.18
        assert abs(dx-30)<=1 and actual['success']
        assert [rect.get(k) for k in ('y','width','height','transform')]==['50','40','30',None]
        accepted=next(r for r in events if r['event']=='accepted' and r['id']=='servo')
        feedback=[r for r in events if r['event']=='servo_feedback']
        row.update(saved_dx=dx,program_ms=(terminal['terminal_ns']-accepted['accepted_ns'])/1e6,
                   local_corrections=sum(r['reason']=='correct' for r in feedback),
                   remote_pointer_replies=sum(r['event']=='command' and r['command']['op']=='pointer_reply' for r in events))
    rows.append(row)
(HERE/'results/servo-interface-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
