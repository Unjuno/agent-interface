#!/usr/bin/env python3
"""Targeted, read-only Vision OCR replay on two retained r02 C task-4 frames."""
from __future__ import annotations
import hashlib, json, platform, subprocess, tempfile, time
from pathlib import Path
from PIL import Image
import Vision
import Quartz
from Foundation import NSURL

PACKAGE=Path(__file__).resolve().parent
REPO=next(p for p in PACKAGE.parents if (p/'.git').exists())
BASE='research/integration/planner_contract_56_4d74_20261004/r02/formal-output'
SETTINGS={'recognition_level':'accurate','recognition_languages':['en-US'],'uses_language_correction':False,'candidate_policy':'top-ranked candidate only; exact token after outer whitespace strip'}
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
with tempfile.TemporaryDirectory(prefix='vision-a04-',dir=REPO/'work') as td:
    td=Path(td)
    for block,state in [('block-1','verify_token'),('block-2','token_entered')]:
        task_path=f'{BASE}/{block}/C/task-4.json'
        task=json.loads(subprocess.check_output(['git','show',f'origin/main:{task_path}']))
        record=next(r for r in task['graph']['raw_observations'] if r['state']==state)
        frame_name=Path(record['raw_observation']['image']).name
        frame_path=f'{BASE}/{block}/C/client/runtime/{frame_name}'
        frame_bytes=subprocess.check_output(['git','show',f'origin/main:{frame_path}'])
        frame_hash=sha(frame_bytes)
        if frame_hash!=record['image_sha256']:
            raise RuntimeError(f'frame hash mismatch: {frame_path}')
        local_frame=td/f'{block}-{frame_name}'
        local_frame.write_bytes(frame_bytes)
        x0,y0,x1,y1=task['graph']['value_crop']
        crop_path=td/f'{block}-crop.png'
        geometry=f'{x1-x0}x{y1-y0}+{x0}+{y0}'
        result=subprocess.run(['magick',str(local_frame),'-crop',geometry,'+repage','-alpha','remove','-colorspace','Gray','-resize','800%','-bordercolor','white','-border','32',str(crop_path)],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        crop_pixels=subprocess.run(['magick',str(crop_path),'-colorspace','Gray','-depth','8','gray:-'],capture_output=True)
        if crop_pixels.returncode:
            raise RuntimeError(crop_pixels.stderr.decode(errors='replace'))
        req=Vision.VNRecognizeTextRequest.alloc().init()
        req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        req.setRecognitionLanguages_(SETTINGS['recognition_languages'])
        req.setUsesLanguageCorrection_(SETTINGS['uses_language_correction'])
        image_source=Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(str(crop_path)),None)
        if image_source is None:
            raise RuntimeError(f'ImageIO could not read crop: {crop_path}')
        cgimage=Quartz.CGImageSourceCreateImageAtIndex(image_source,0,None)
        if cgimage is None:
            raise RuntimeError(f'ImageIO could not decode crop: {crop_path}')
        handler=Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cgimage,None)
        vision_started=time.perf_counter_ns()
        success,error=handler.performRequests_error_([req],None)
        vision_elapsed=time.perf_counter_ns()-vision_started
        if not success:
            raise RuntimeError(f'Vision request failed: {error}')
        candidates=[]
        for observation in (req.results() or []):
            top=observation.topCandidates_(1)
            if top:
                c=top[0]
                candidates.append({'text':str(c.string()),'confidence':float(c.confidence())})
        top_text=candidates[0]['text'] if candidates else ''
        rows.append({'block':block,'task_id':task['task']['task_id'],'state':state,'expected_token':task['task']['token'],'model_crop':task['graph']['value_crop'],'source_git_path':frame_path,'source_sha256':frame_hash,'crop_geometry':geometry,'crop_pixel_sha256':sha(crop_pixels.stdout),'a03_tesseract_text':record['ocr']['stdout'].strip(),'vision_candidates':candidates,'vision_elapsed_ns':vision_elapsed,'vision_top_exact':top_text.strip()==task['task']['token']})
version=subprocess.check_output(['sw_vers','-productVersion'],text=True).strip()
build=subprocess.check_output(['sw_vers','-buildVersion'],text=True).strip()
raw={'experiment_id':'layout_b_vision_r02_transfer_a04_20261004','classification':'targeted retrospective failure-case diagnostic; not qualification','host':{'os_version':version,'os_build':build,'architecture':platform.machine()},'bridge':'pyobjc-framework-Vision 12.2.2','framework':'Apple Vision (system-provided OCR model; internal model version not exposed)','settings':SETTINGS,'preprocess':'model-authored value_crop; alpha remove; grayscale; resize 800%; 32px white border','rows':rows,'disposition':'PASS_TARGETED_TWO_CASE_RESCUE' if all(r['vision_top_exact'] for r in rows) else 'FAIL_TARGETED_TWO_CASE_RESCUE'}
(PACKAGE/'RAW.json').write_text(json.dumps(raw,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(raw,indent=2,ensure_ascii=False))
