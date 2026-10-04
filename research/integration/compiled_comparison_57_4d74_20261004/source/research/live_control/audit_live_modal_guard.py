"""Audit retained guard samples, exact observations and post-controller artifacts."""
import hashlib,json
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;report=[]
for cohort in ('live-modal-guard-01','live-modal-guard-02'):
    root=HERE/'results'/cohort
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
    for row in json.loads((root/'results.json').read_text()):
        d=root/row['case'];events=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()];decoder=Decoder('live-control');count=0
        for event in events:
            if event['event']!='observation':continue
            count+=1;f=decoder.accept((d/f'{count:03d}.ait').read_bytes())
            with Image.open(d/Path(event['image']).name) as im:assert im.size==(f.width,f.height) and im.tobytes()==f.pixels
        wb=load_workbook(d/'sheet.xlsx');values=[wb.active['A1'].value,wb.active['A2'].value]
        assert values==([532,590] if row['case']=='normal' else [None,None])
        guard=row['guard'];sample_hash=None
        if cohort.endswith('02'):
            sample=d/'confirm-guard.png';sample_hash=hashlib.sha256(sample.read_bytes()).hexdigest()
            with Image.open(sample) as im:assert im.size==(1280,800)
            if row['case']!='normal':assert guard['input_before']['revision']==guard['input_after']['revision']
        report.append(dict(cohort=cohort,case=row['case'],frames=count,guard=guard['status'],saved_values=values,guard_sample_sha256=sample_hash))
(HERE/'results/live-modal-guard-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
