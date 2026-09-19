"""Audit all retained integration attempts, including incomplete setup cohort."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent
summary=[]
for n in (1,2,3):
    root=HERE/f'results/patch-servo-{n:02d}'
    manifest=root/'sources.json'
    if manifest.exists():
        for name,h in json.loads(manifest.read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for offset in (0,40):
        out=root/str(offset);events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
        decoder=Decoder('live-control');count=0
        for r in events:
            if r['event']!='observation':continue
            count+=1;assert r['sequence']==count
            f=decoder.accept((out/f'{count:03d}.ait').read_bytes())
            with Image.open(out/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
        assert all(r['release']['verified'] for r in events if r['event']=='terminal')
        row={'cohort':n,'offset':offset,'exact_frames':count,'source_manifest_present':manifest.exists()}
        result=out/'result.json'
        if result.exists():
            v=json.loads(result.read_text());rect=ET.parse(out/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
            assert all(rect.get(k)==value for k,value in v['after'].items())
            assert v['preserved']
            if n==3:assert v['precision_pass'] and v['controller'][-1]['reason']=='local_goal_reached'
            row.update(precision_pass=v['precision_pass'],reason=v['controller'][-1]['reason'],program_ms=v['program_ms'])
        else:
            assert n==2 and offset==40
            row['reason']='setup rejected: 41 points exceeds 32; no servo trial'
        summary.append(row)
(HERE/'results/patch-servo-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
