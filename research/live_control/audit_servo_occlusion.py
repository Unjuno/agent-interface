"""Audit overlay fault evidence including normal-control and false local-goal cases."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;rows=[]
for cohort in ('servo-occlusion-01','servo-occlusion-control-01','servo-occlusion-02'):
    root=HERE/'results'/cohort
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for out in sorted(p for p in root.iterdir() if p.is_dir()):
        events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()];count=0;decoder=Decoder('live-control')
        for r in events:
            if r['event']!='observation':continue
            count+=1;assert count==r['sequence']
            f=decoder.accept((out/f'{count:03d}.ait').read_bytes())
            with Image.open(out/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
        assert all(r['release']['verified'] for r in events if r['event']=='terminal')
        result=json.loads((out/'result.json').read_text());rect=ET.parse(out/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
        assert all(rect.get(k)==v for k,v in result['actual'].items())
        assert [rect.get(k) for k in ('y','width','height','transform')]==['50','40','30',None]
        if cohort=='servo-occlusion-02' and out.name=='normal':assert result['precision_pass']
        else:assert result['saved_dx']==0
        reason=result['controller'][-1]['reason']
        if cohort=='servo-occlusion-02' and out.name=='replacement':assert reason=='local_goal_reached' and not result['precision_pass']
        rows.append(dict(cohort=cohort,case=out.name,exact_frames=count,status=result['terminal']['status'],reason=reason,saved_dx=result['saved_dx'],precision_pass=result['precision_pass']))
(HERE/'results/servo-occlusion-audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
