#!/usr/bin/env python3
"""Independent raw-only audit of construction allocation 2447017."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROI=(slice(20,300),slice(20,620))
MAX_DT_MS=100.0
MIN_TRACKS=80
DROP_DY=-20.0
WRONG_LEFT_DX=20.0


def lk(a_path: Path,b_path: Path) -> dict:
    a=np.asarray(Image.open(a_path).convert('L'),dtype=np.uint8)[ROI]
    b=np.asarray(Image.open(b_path).convert('L'),dtype=np.uint8)[ROI]
    points=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if points is None:return {'valid_tracks':0,'median_dx_px':None,'median_dy_px':None}
    moved,status,_=cv2.calcOpticalFlowPyrLK(a,b,points,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if moved is None or status is None:return {'valid_tracks':0,'median_dx_px':None,'median_dy_px':None}
    delta=moved[status[:,0]==1,0,:]-points[status[:,0]==1,0,:]
    if len(delta):delta=delta[np.hypot(delta[:,0],delta[:,1])<100]
    n=int(len(delta))
    if n<MIN_TRACKS:return {'valid_tracks':n,'median_dx_px':None,'median_dy_px':None}
    return {'valid_tracks':n,'median_dx_px':float(statistics.median(delta[:,0])),
            'median_dy_px':float(statistics.median(delta[:,1]))}


def main(root: Path, output: Path) -> int:
    errors=[]
    score_path=root/'score.json'
    if not score_path.exists():
        result={'schema':'issue2447-wrong-direction-audit-v1','decision':'STOP_NO_SCORE',
                'errors':['missing_score'],'formal_rows':0,'retries':0}
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(json.dumps(result,sort_keys=True));return 0
    score=json.loads(score_path.read_text(encoding='utf-8'))
    if score.get('seed')!=2447017 or score.get('gate')!='temporal_gate' or score.get('class')!='drop':errors.append('case_identity')
    if score.get('error') is not None:errors.append('runner_error')
    phase_dir=root/'phase1';phase_path=phase_dir/'result.json'
    phase_audit={'reported_status':None,'reconstructed_status':'UNKNOWN','pairs':[],'eligible_pairs':0}
    if not phase_path.exists():
        decision='STOP_SETUP_OR_PHASE_NOT_REACHED'
        if (root/'next_subgoal').exists():errors.append('action_without_phase_evidence')
    else:
        phase=json.loads(phase_path.read_text(encoding='utf-8'))
        names=phase.get('frame_files',[]);times=phase.get('frame_capture_start_ns',[])
        if len(names)!=len(times) or len(names)<2:errors.append('phase_frame_receipt_incomplete')
        pairs=[]
        for i,(left_name,right_name) in enumerate(zip(names,names[1:])):
            m=lk(phase_dir/left_name,phase_dir/right_name)
            gap=(times[i+1]-times[i])/1e6
            eligible=gap<=MAX_DT_MS and m['valid_tracks']>=MIN_TRACKS and m['median_dy_px'] is not None
            pairs.append({'pair':i,'gap_ms':gap,**m,'eligible':eligible,
                          'drop':bool(eligible and m['median_dy_px']<=DROP_DY)})
        valid=[p for p in pairs if p['eligible']]
        computed='DROP_COMPLETED' if any(p['drop'] for p in valid) else ('NO_DROP' if valid else 'UNKNOWN')
        phase_audit={'reported_status':phase.get('temporal_status'),
                     'reconstructed_status':computed,'pairs':pairs,'eligible_pairs':len(valid)}
        if computed!=phase.get('temporal_status'):errors.append('phase_status_mismatch')
        if score.get('phase1',{}).get('temporal_status')!=computed:errors.append('score_phase_status_mismatch')
        if computed!='DROP_COMPLETED' or phase.get('extra_forward_needed') is True:
            decision='STOP_PHASE_NOT_CONFIRMED'
            if (root/'next_subgoal').exists():errors.append('fault_action_before_confirmed_phase')
        else:
            action=root/'next_subgoal';receipt_path=action/'result.json'
            if not receipt_path.exists():
                decision='HOLD_WRONG_DIRECTION_EFFECT_MISSING';errors.append('missing_fault_action_receipt')
            else:
                receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
                before=action/'before-action.png';after=action/'after-action.png'
                if not before.exists() or not after.exists():
                    effect={'valid_tracks':0,'median_dx_px':None,'median_dy_px':None}
                    errors.append('paired_action_images_missing')
                else:
                    effect=lk(before,after)
                    pixel_sha=hashlib.sha256(Image.open(before).convert('RGB').tobytes()).hexdigest()
                    if pixel_sha!=receipt.get('observation_sha256'):errors.append('fresh_image_hash_mismatch')
                if receipt.get('key')!='Left':errors.append('wrong_fault_key')
                if receipt.get('observation_binding')!=score.get('setup_binding'):errors.append('observation_binding_mismatch')
                ordered=bool(receipt.get('observation_ns',0)<receipt.get('down_done_ns',0)<=receipt.get('up_started_ns',0)<receipt.get('release_done_ns',0)<=score.get('next_subgoal_after_action_ns',0))
                if not ordered:errors.append('action_observation_release_order')
                release=receipt.get('release',{})
                if not (release.get('verified') and not release.get('keys_down') and not release.get('buttons_down')):errors.append('release_not_verified_empty')
                visual_wrong=effect['valid_tracks']>=MIN_TRACKS and effect['median_dx_px'] is not None and effect['median_dx_px']>=WRONG_LEFT_DX
                if visual_wrong and score.get('handoff_after_wrong_direction')=='STOP_WRONG_DIRECTION' and score.get('third_subgoal_emitted') is False and not (root/'third_subgoal').exists() and score.get('next_subgoal_yaw_delta',0)>0:
                    decision='PASS_WRONG_DIRECTION_FAIL_CLOSED_STOP'
                else:
                    decision='HOLD_WRONG_DIRECTION_EFFECT_UNRESOLVED'
                    if score.get('third_subgoal_emitted') is not False or (root/'third_subgoal').exists():errors.append('third_subgoal_emitted_after_fault')
                score['independent_turn_flow']=effect

    owner_records=[]
    for relpath in ('setup-owner-records.json','phase1/owner-records.json','phase2/owner-records.json','next_subgoal/owner-records.json'):
        path=root/relpath
        if path.exists():owner_records.extend(json.loads(path.read_text(encoding='utf-8')))
    releases=[r for r in owner_records if r.get('event')=='owner_release']
    all_empty=bool(releases) and all(r.get('verified') is True and not r.get('keys_down') and not r.get('buttons_down') for r in releases)
    if releases and not all_empty:errors.append('owner_release_not_empty')
    if decision=='PASS_WRONG_DIRECTION_FAIL_CLOSED_STOP' and not all_empty:
        decision='FAIL_INPUT_CLEANUP'
    if decision.startswith('PASS') and errors:decision='HOLD_AUDIT_ERRORS'
    report={'schema':'issue2447-wrong-direction-audit-v1','allocation':'issue2447-wrong-direction-construction-2447017',
            'decision':decision,'errors':errors,'phase':phase_audit,
            'controller_visible_direction_evidence':score.get('independent_turn_flow',score.get('controller_visible_direction_evidence')),
            'handoff_decision':score.get('handoff_after_wrong_direction'),
            'third_subgoal_emitted':score.get('third_subgoal_emitted'),
            'release_count':len(releases),'all_releases_verified_empty':all_empty,
            'formal_rows':0,'retries':0,
            'scope':'One fresh construction-only wrong-direction injection, or a recorded precondition STOP. Not a comparative rate, general safety claim, recovery/transfer result, or Issue #2447 acceptance.'}
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,sort_keys=True))
    return 0 if not errors else 1


if __name__=='__main__':raise SystemExit(main(Path(sys.argv[1]),Path(sys.argv[2])))
