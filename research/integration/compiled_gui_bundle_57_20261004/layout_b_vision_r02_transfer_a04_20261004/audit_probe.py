#!/usr/bin/env python3
"""Replay and audit two selected pre-submit r02 screenshots with macOS Vision."""
from __future__ import annotations
import hashlib, json, platform, subprocess, tempfile, time
from pathlib import Path
import Vision
import Quartz
from Foundation import NSURL

PACKAGE=Path(__file__).resolve().parent
REPO=next(p for p in PACKAGE.parents if (p/'.git').exists())
RAW=json.loads((PACKAGE/'RAW.json').read_text())
BASE='research/integration/planner_contract_56_4d74_20261004/r02/formal-output'
sha=lambda b:hashlib.sha256(b).hexdigest()
problems=[]
if RAW['host']['architecture']!=platform.machine(): problems.append('architecture')
if RAW['host']['os_version']!=subprocess.check_output(['sw_vers','-productVersion'],text=True).strip(): problems.append('os_version')
if RAW['host']['os_build']!=subprocess.check_output(['sw_vers','-buildVersion'],text=True).strip(): problems.append('os_build')
for index,(block,state) in enumerate([('block-1','verify_token'),('block-2','token_entered')]):
    try:
        saved=RAW['rows'][index]
        task_path=f'{BASE}/{block}/C/task-4.json'
        task=json.loads(subprocess.check_output(['git','show',f'origin/main:{task_path}']))
        record=next(r for r in task['graph']['raw_observations'] if r['state']==state)
        frame_path=saved['source_git_path']
        blob=subprocess.check_output(['git','show',f'origin/main:{frame_path}'])
        if sha(blob)!=saved['source_sha256'] or sha(blob)!=record['image_sha256']:
            problems.append(f'frame_hash:{block}'); continue
        if task['task']['token']!=saved['expected_token'] or task['graph']['value_crop']!=saved['model_crop']:
            problems.append(f'task_or_crop:{block}'); continue
        if record['ocr']['stdout'].strip()!=saved['a03_tesseract_text']:
            problems.append(f'tesseract_reference:{block}')
        if any(e.get('action')=='submit_form' or e.get('action')=='save_value' for e in task['graph']['events']):
            problems.append(f'submitted_before_capture:{block}')
        with tempfile.TemporaryDirectory(prefix='vision-a04-audit-',dir=REPO/'work') as td:
            td=Path(td); frame=td/'frame.png'; frame.write_bytes(blob)
            x0,y0,x1,y1=task['graph']['value_crop']
            crop=td/'crop.png'; geom=f'{x1-x0}x{y1-y0}+{x0}+{y0}'
            p=subprocess.run(['magick',str(frame),'-crop',geom,'+repage','-alpha','remove','-colorspace','Gray','-resize','800%','-bordercolor','white','-border','32',str(crop)],capture_output=True,text=True)
            if p.returncode: problems.append(f'magick:{block}'); continue
            px=subprocess.run(['magick',str(crop),'-colorspace','Gray','-depth','8','gray:-'],capture_output=True)
            if px.returncode or sha(px.stdout)!=saved['crop_pixel_sha256']:
                problems.append(f'crop_hash:{block}'); continue
            image_source=Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(str(crop)),None)
            cgimage=Quartz.CGImageSourceCreateImageAtIndex(image_source,0,None) if image_source is not None else None
            if cgimage is None: problems.append(f'imageio:{block}'); continue
            req=Vision.VNRecognizeTextRequest.alloc().init()
            req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            req.setRecognitionLanguages_(['en-US'])
            req.setUsesLanguageCorrection_(False)
            handler=Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cgimage,None)
            ok,error=handler.performRequests_error_([req],None)
            if not ok: problems.append(f'vision:{block}:{error}'); continue
            candidates=[]
            for obs in req.results() or []:
                top=obs.topCandidates_(1)
                if top: candidates.append({'text':str(top[0].string()),'confidence':float(top[0].confidence())})
            if candidates!=saved['vision_candidates']:
                problems.append(f'candidate_replay:{block}')
            top=candidates[0]['text'] if candidates else ''
            if (top.strip()==task['task']['token'])!=saved['vision_top_exact']:
                problems.append(f'exact_oracle:{block}')
    except Exception as exc:
        problems.append(f'exception:{block}:{type(exc).__name__}:{exc}')
result={'experiment_id':RAW['experiment_id'],'status':'PASS_REPRODUCED_TARGETED_DIAGNOSTIC_ONLY' if not problems else 'FAIL_AUDIT','rows':len(RAW['rows']),'problems':problems,'limits':['selected after task-4 OCR failures were known','two post-entry screenshots and no source-frame controls','no Submit action or independent effect result','macOS Vision is not directly portable to the WSLc comparison host']}
(PACKAGE/'AUDIT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,indent=2,ensure_ascii=False))
raise SystemExit(0 if not problems else 1)
