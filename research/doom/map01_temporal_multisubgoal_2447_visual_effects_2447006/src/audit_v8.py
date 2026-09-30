"""Posthoc raw-only audit combining phase transition and paired visual effects."""
from pathlib import Path
import argparse, hashlib, json
import cv2
import numpy as np
from PIL import Image

ROI=(20,300,20,620); MIN_TRACKS=80; DY_THRESHOLD=-20.0; MAX_PAIR_DT_MS=100.0

def flow(a,b):
    x=np.asarray(a.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    y=np.asarray(b.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    p=cv2.goodFeaturesToTrack(x,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if p is None:return {'valid_tracks':0,'median_dx_px':None,'median_dy_px':None,'status':'UNKNOWN'}
    q,s,_=cv2.calcOpticalFlowPyrLK(x,y,p,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if q is None or s is None:return {'valid_tracks':0,'median_dx_px':None,'median_dy_px':None,'status':'UNKNOWN'}
    d=q[s[:,0]==1,0,:]-p[s[:,0]==1,0,:]
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=len(d)
    if n<MIN_TRACKS:return {'valid_tracks':int(n),'median_dx_px':None,'median_dy_px':None,'status':'UNKNOWN'}
    return {'valid_tracks':int(n),'median_dx_px':float(np.median(d[:,0])),'median_dy_px':float(np.median(d[:,1])),'status':'MEASURED'}

def audit(root):
    root=Path(root); score=json.loads((root/'score.json').read_text());errors=[]
    if score.get('seed')!=2447006 or score.get('gate')!='temporal_gate' or score.get('class')!='drop':errors.append('case_identity')
    if score.get('error') is not None:errors.append('runner_error')
    phase=root/'phase1';pr=json.loads((phase/'result.json').read_text());frames=[Image.open(phase/n).convert('RGB') for n in pr['frame_files']]
    pairs=[]
    for i,(a,b) in enumerate(zip(frames,frames[1:])):
        dt=(pr['frame_capture_start_ns'][i+1]-pr['frame_capture_start_ns'][i])/1e6
        m=flow(a,b);m['i0']=i;m['i1']=i+1;m['dt_ms']=dt;pairs.append(m)
    eligible=[r for r in pairs if r['dt_ms']<=MAX_PAIR_DT_MS and r['valid_tracks']>=MIN_TRACKS and r['median_dy_px'] is not None]
    detected=any(r['median_dy_px']<=DY_THRESHOLD for r in eligible)
    if not detected or pr.get('temporal_status')!='DROP_COMPLETED' or score.get('extra_forward_issued') is not False:errors.append('temporal_gate_raw_recompute')
    before=score.get('before',{});after=score.get('after_phase1',{})
    physical=bool(before.get('sector')==165 and before.get('z')==-64.0 and after.get('sector')!=165 and after.get('z',0)<=-120.0)
    if not physical:errors.append('scorer_drop_transition')
    turns=[]
    for name,key,relkey,afterkey in [('next_subgoal','Right','next_subgoal_release_done_ns','next_subgoal_after_action_ns'),('third_subgoal','Left','third_subgoal_release_done_ns','third_subgoal_after_action_ns')]:
        d=root/name;r=json.loads((d/'result.json').read_text());bf=d/'before-action.png';af=d/'after-action.png'
        bimg=Image.open(bf).convert('RGB') if bf.exists() else None;aimg=Image.open(af).convert('RGB') if af.exists() else None
        rawhash=None if bimg is None else hashlib.sha256(np.asarray(bimg).tobytes()).hexdigest()
        binding={k:score.get('setup_binding',{}).get(k) for k in ('focus','surface','geometry')}
        release=r.get('release',{})
        ordered=bool(r.get('observation_ns',0)<r.get('down_done_ns',0)<=r.get('up_started_ns',0)<r.get('release_done_ns',0)<=score.get(afterkey,0))
        f=None if bimg is None or aimg is None else flow(bimg,aimg)
        row={'name':name,'key':r.get('key'),'before_matches_fresh_receipt':bool(rawhash and rawhash==r.get('observation_sha256')),
             'binding_matches_setup':r.get('observation_binding')==binding,'ordered_observation_action_release_images':ordered,
             'release_verified_empty':bool(release.get('verified') and not release.get('keys_down') and not release.get('buttons_down')),
             'visual_flow':f}
        turns.append(row)
        if r.get('key')!=key:errors.append(name+':key')
        if not row['before_matches_fresh_receipt']:errors.append(name+':fresh_image_hash')
        if not row['binding_matches_setup']:errors.append(name+':binding')
        if not ordered:errors.append(name+':order')
        if not row['release_verified_empty']:errors.append(name+':release')
        if f is None or f['status']!='MEASURED':errors.append(name+':visual_flow_unavailable')
    result={'schema':'issue2447-visual-effects-audit-v2','case':'issue2447-visual-effects-construction-2447006',
            'decision':'PASS_CONSTRUCTION_INSTRUMENTATION' if not errors else 'HOLD_CONSTRUCTION_INSTRUMENTATION',
            'errors':errors,'phase':{'eligible_pairs':len(eligible),'drop_pair_indices':[r['i0'] for r in eligible if r['median_dy_px']<=DY_THRESHOLD],
                'raw_frame_recompute_matches':detected},'drop_effect':{'before_sector_z':[before.get('sector'),before.get('z')],
                'after_sector_z':[after.get('sector'),after.get('z')],'transition_observed':physical},
            'turns':turns,'formal_rows':0,'retries':0,
            'scope':'One construction episode and instrumentation check only; not a comparison study, issue acceptance, safety estimate, or task-completion claim.'}
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    r=audit(a.evidence);Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))

if __name__=='__main__':main()
