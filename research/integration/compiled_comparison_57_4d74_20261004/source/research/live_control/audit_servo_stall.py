"""Audit both stall candidates and positive/lost tracking regressions."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
rows=[]
for cohort in ('servo-stall-01','servo-stall-02','servo-outcome-02'):
    root=HERE/'results'/cohort
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for out in sorted(p for p in root.iterdir() if p.is_dir()):
        events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()];count=0;decoder=Decoder('live-control')
        for r in events:
            if r['event']!='observation':continue
            count+=1;assert count==r['sequence']
            f=decoder.accept((out/f'{count:03d}.ait').read_bytes())
            with Image.open(out/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
        terminals=[r for r in events if r['event']=='terminal'];assert all(r['release']['verified'] for r in terminals)
        terminal=next(r for r in terminals if r['id']=='servo')
        if cohort=='servo-stall-01':expected='failed'
        elif cohort=='servo-stall-02':expected={'yield_timeout':'needs_decision','feedback_timeout':'needs_decision','yield_expiry':'expired','yield_cancel':'cancelled'}[out.name]
        else:expected='completed' if out.name=='0' else 'needs_decision'
        assert terminal['status']==expected
        if cohort.startswith('servo-stall'):
            assert not any(r.get('operation')=='continue_move' or r.get('continuation') for r in events)
            result=next(r for r in json.loads((root/'results.json').read_text()) if r['case']==out.name)
            assert result['released_while_output_blocked'] and result['no_late_motion']
        else:
            result=json.loads((out/'result.json').read_text());assert result['preserved']
            assert result['precision_pass']==(out.name=='0')
        rows.append({'cohort':cohort,'case':out.name,'exact_frames':count,'status':terminal['status']})
(HERE/'results/servo-stall-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
