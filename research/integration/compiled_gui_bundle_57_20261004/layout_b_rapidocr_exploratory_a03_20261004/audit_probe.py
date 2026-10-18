#!/usr/bin/env python3
"""Replay and audit the retrospective RapidOCR A03 output."""
from __future__ import annotations
import hashlib, json, subprocess, tempfile
from collections import defaultdict
from pathlib import Path
from PIL import Image
import numpy as np
from rapidocr import RapidOCR

PACKAGE=Path(__file__).resolve().parent
REPO=next(p for p in PACKAGE.parents if (p/'.git').exists())
RAW=json.loads((PACKAGE/'RAW.json').read_text())
A02=json.loads((REPO/'research/integration/compiled_gui_bundle_57_20261004/layout_b_ocr_construction_a02_20261004/RAW.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
problems=[]
models_dir=Path(__import__('rapidocr').__file__).resolve().parent/'models'
actual_models=[{'file':p.name,'sha256':sha(p.read_bytes()),'size_bytes':p.stat().st_size} for p in sorted(models_dir.glob('*.onnx'))]
if actual_models != RAW['model_files']: problems.append('model_files')
expected={(r['arm'],r['task_id'],r['frame']):r for r in A02['heldout_rows']}
if len(RAW['rows']) != 56: problems.append('row_count')
if len({r['frame'] for r in RAW['rows']}) != len(RAW['rows']): problems.append('duplicate_frame')
engine=RapidOCR()
replayed=[]
with tempfile.TemporaryDirectory(prefix='rapidocr-a03-audit-',dir=REPO/'work') as td:
    td=Path(td)
    for i,row in enumerate(RAW['rows']):
        key=(row['arm'],row['task_id'],row['frame'])
        a02=expected.get(key)
        if a02 is None: problems.append(f'not_in_a02:{key}'); continue
        frame=REPO/row['frame']
        frame_hash=sha(frame.read_bytes())
        if frame_hash != row['frame_sha256'] or frame_hash != a02['frame_sha256']:
            problems.append(f'frame_hash:{row["frame"]}'); continue
        crop=td/f'{i:03}.png'
        cmd=['magick',str(frame),'-crop','280x26+499+546','+repage','-alpha','remove','-colorspace','Gray','-resize','800%','-bordercolor','white','-border','32',str(crop)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        if p.returncode: problems.append(f'magick:{row["frame"]}'); continue
        pixels=subprocess.run(['magick',str(crop),'-colorspace','Gray','-depth','8','gray:-'],capture_output=True)
        if pixels.returncode: problems.append(f'pixels:{row["frame"]}'); continue
        pixel_hash=sha(pixels.stdout)
        if pixel_hash != row['crop_pixel_sha256'] or pixel_hash != a02['crop_pixel_sha256']:
            problems.append(f'crop_hash:{row["frame"]}'); continue
        res=engine(np.asarray(Image.open(crop).convert('RGB')))
        texts=list(res.txts or [])
        joined=''.join(texts)
        if texts != row['rapidocr_texts'] or joined != row['joined_text']:
            problems.append(f'ocr_replay:{row["frame"]}')
        exact=joined.strip()==row['expected_token']
        if exact != row['exact_match'] or row['expected_token'] != a02['expected_token']:
            problems.append(f'oracle:{row["frame"]}')
        replayed.append({**row,'a02_tesseract_exact':a02['exact_match']})

cases=defaultdict(list)
for row in replayed: cases[(row['arm'],row['task_id'])].append(row)
case_summary={f'{arm}/{task}':{'rapid_exact_frames':[Path(r['frame']).name for r in rs if r['exact_match']], 'tesseract_exact_frames':[Path(r['frame']).name for r in rs if r['a02_tesseract_exact']], 'union_exact':any(r['exact_match'] or r['a02_tesseract_exact'] for r in rs), 'source_exact_frames':[Path(r['frame']).name for r in rs if r['is_task_source_frame'] and (r['exact_match'] or r['a02_tesseract_exact'])]} for (arm,task),rs in cases.items()}
if len(case_summary)!=6: problems.append('case_count')
if any(not x['union_exact'] for x in case_summary.values()): problems.append('union_case_coverage')
if any(x['source_exact_frames'] for x in case_summary.values()): problems.append('source_false_positive')
result={'experiment_id':'layout_b_rapidocr_exploratory_a03_20261004','status':'PASS_REPRODUCED_EXPLORATORY_ONLY' if not problems else 'FAIL_AUDIT','replayed_rows':len(replayed),'case_summary':case_summary,'problems':problems,'limitations':['retrospective previously inspected single-run screenshots','plain-arm positive capture-to-POST timing unverified','not a live/input/effect/latency/efficiency qualification']}
(PACKAGE/'AUDIT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,indent=2,ensure_ascii=False))
raise SystemExit(0 if not problems else 1)
