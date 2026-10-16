"""Audit wrong-anchor evidence and narrow source-ambiguity regression."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;rows=[]
for n in (2,3):
    root=HERE/f'results/servo-distractor-{n:02d}'
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for color in ('blue','red'):
        out=root/color;events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');count=0
        for r in events:
            if r['event']!='observation':continue
            count+=1;assert r['sequence']==count
            f=decoder.accept((out/f'{count:03d}.ait').read_bytes())
            with Image.open(out/Path(r['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
        result=json.loads((out/'result.json').read_text())
        for rect in ET.parse(out/'shape.svg').getroot().findall('{http://www.w3.org/2000/svg}rect'):
            assert all(rect.get(k)==v for k,v in result['saved'][rect.get('id')].items())
        assert result['collateral_preserved']
        assert all(r['release']['verified'] for r in events if r['event']=='terminal')
        if color=='red' and n==2:assert abs(result['target_dx']+48)<1
        if color=='red' and n==3:
            assert result['terminal']['status']=='rejected' and result['target_dx']==0
            assert not any(r.get('id')=='servo' and r['event'] in ('accepted','pointer_admission') for r in events)
        rows.append({'cohort':n,'color':color,'exact_frames':count,'status':result['terminal']['status'],'target_dx':result['target_dx'],'precision_pass':result['precision_pass']})
(HERE/'results/servo-distractor-audit.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
