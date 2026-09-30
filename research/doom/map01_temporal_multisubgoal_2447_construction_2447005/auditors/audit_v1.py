from pathlib import Path
import argparse,hashlib,json,statistics
import cv2,numpy as np
from PIL import Image
ROI=(20,300,20,620);MIN_TRACKS=80;DY_THRESHOLD=-20.0;MAX_PAIR_DT_MS=100.0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def derr(t,c):return ((t-c+180)%360)-180

def metric(a,b):
    a=np.asarray(a.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]];b=np.asarray(b.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    ok=st[:,0]==1;p=pts[ok][:,0,:];q=p2[ok][:,0,:];d=q-p
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=int(len(d));med=None if n==0 else float(np.median(d[:,1]));status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP')
    return {'valid_tracks':n,'median_dy_px':med,'status':status}

def audit_case(case_dir,row):
    p=Path(case_dir);errs=[]
    score=json.loads((p/'score.json').read_text())
    for k in ('seed','gate'):
        if score.get(k)!=row[k]:errs.append(f'{k}_mismatch')
    if score.get('class')!=row['class']:errs.append('class_mismatch')
    expected_heading=row.get('heading')
    if score.get('requested_heading')!=expected_heading:errs.append('heading_mismatch')
    if score.get('error') is not None:errs.append('runner_error')
    pr=score.get('phase1',{});p1=p/'phase1'
    files=pr.get('frame_files',[]);starts=pr.get('frame_capture_start_ns',[])
    if len(files)<2 or len(files)!=len(starts):errs.append('frame_manifest')
    else:
        ims=[Image.open(p1/f).convert('RGB') for f in files]
        consec=[]
        for i in range(1,len(ims)):
            m=metric(ims[i-1],ims[i]);m['dt_ms']=(starts[i]-starts[i-1])/1e6;consec.append(m)
        elig=[m for m in consec if m['dt_ms']<=MAX_PAIR_DT_MS and m['valid_tracks']>=MIN_TRACKS and m['median_dy_px'] is not None]
        temporal='DROP_COMPLETED' if any(m['median_dy_px']<=DY_THRESHOLD for m in elig) else ('UNKNOWN' if not elig else 'NO_DROP')
        endpoint=metric(ims[0],ims[-1])
        if temporal!=pr.get('temporal_status'):errs.append('temporal_recompute')
        if endpoint['status']!=pr.get('endpoint',{}).get('status'):errs.append('endpoint_recompute')
        selected=endpoint['status'] if row['gate']=='endpoint_gate' else temporal
        expected_extra=selected!='DROP_COMPLETED'
        if bool(score.get('extra_forward_issued'))!=expected_extra:errs.append('gate_action_mismatch')
        if (p/'phase2').exists()!=expected_extra:errs.append('phase2_presence')
    if row['class']=='drop' and not score.get('hidden_phase1_drop'):errs.append('positive_no_drop')
    if row['class']=='wall' and score.get('hidden_phase1_drop'):errs.append('wall_false_drop')
    nres=json.loads((p/'next_subgoal'/'result.json').read_text()) if (p/'next_subgoal'/'result.json').exists() else {}
    if not nres.get('next_subgoal_issued'):errs.append('next_missing')
    rel=nres.get('release',{})
    if not rel.get('verified') or rel.get('keys_down') or rel.get('buttons_down'):errs.append('next_release')
    nevents=json.loads((p/'next_subgoal'/'events.json').read_text()) if (p/'next_subgoal'/'events.json').exists() else []
    if len(nevents)!=1 or nevents[0].get('purpose')!='subgoal_turn_right' or nevents[0].get('keys')!=['Right']:errs.append('next_event_shape')
    if nr.get('key')!='Right' or not nr.get('observation_sha256'):errs.append('next_observation')
    try:
        obs=Image.open(p/'next_subgoal'/'handoff-observation.png').convert('RGB')
        if hashlib.sha256(np.asarray(obs).tobytes()).hexdigest()!=nr.get('observation_sha256'):errs.append('next_observation_hash')
    except Exception:errs.append('next_observation_image')
    if abs(float(score.get('next_subgoal_yaw_delta',0)))<5:errs.append('next_yaw_effect')
    third=json.loads((p/'third_subgoal'/'result.json').read_text()) if (p/'third_subgoal'/'result.json').exists() else {}
    if third.get('key')!='Left' or not third.get('observation_sha256'):errs.append('third_observation')
    if len(third.get('observation_sha256',''))!=64:errs.append('third_observation_hash')
    if third.get('observation_binding')!=score.get('setup_binding'):errs.append('third_observation_binding')
    try:
        obs=Image.open(p/'third_subgoal'/'handoff-observation.png').convert('RGB')
        if hashlib.sha256(np.asarray(obs).tobytes()).hexdigest()!=third.get('observation_sha256'):errs.append('third_observation_hash')
    except Exception:errs.append('third_observation_image')
    if abs(float(score.get('third_subgoal_yaw_delta',0)))<5:errs.append('third_yaw_effect')
    trel=third.get('release',{})
    if not trel.get('verified') or trel.get('keys_down') or trel.get('buttons_down'):errs.append('third_release')
    tevents=json.loads((p/'third_subgoal'/'events.json').read_text()) if (p/'third_subgoal'/'events.json').exists() else []
    if len(tevents)!=1 or tevents[0].get('purpose')!='subgoal_turn_left' or tevents[0].get('keys')!=['Left']:errs.append('third_event_shape')
    if not score.get('controller_release_ok') or not score.get('setup_release_ok'):errs.append('release_integrity')
    if not isinstance(score.get('workflow_release_elapsed_ms'),(int,float)) or score['workflow_release_elapsed_ms']<=0:errs.append('timing')
    return score,errs

def aggregate(evidence,schedule,freeze=None):
    rows=json.loads(Path(schedule).read_text());errs=[];scores=[]
    seen=set()
    for r in rows:
        if r['id'] in seen:errs.append('duplicate_id');continue
        seen.add(r['id']);p=Path(evidence)/r['id']
        if not p.exists():errs.append(f"{r['id']}:missing");continue
        s,e=audit_case(p,r);scores.append((r,s));errs.extend(f"{r['id']}:{x}" for x in e)
    if freeze:
        fr=json.loads(Path(freeze).read_text())
        for rel,h in fr.get('source_sha256',{}).items():
            if sha(Path(fr['source_root'])/rel)!=h:errs.append(f'source_hash:{rel}')
    discr=[(r,s) for r,s in scores if r['class']=='drop' and r.get('heading') in (55,75)]
    temporal=[s for r,s in discr if r['gate']=='temporal_gate'];endpoint=[s for r,s in discr if r['gate']=='endpoint_gate']
    gates={}
    gates['temporal_extra_0_of_4']=len(temporal)==4 and sum(bool(s['extra_forward_issued']) for s in temporal)==0
    gates['endpoint_extra_ge_3_of_4']=len(endpoint)==4 and sum(bool(s['extra_forward_issued']) for s in endpoint)>=3
    pairs={}
    for r,s in discr:pairs.setdefault((r['heading'],r['seed']),{})[r['gate']]=s
    reductions=[]
    for k,v in sorted(pairs.items()):
        if set(v)=={'endpoint_gate','temporal_gate'}:reductions.append(v['endpoint_gate']['workflow_release_elapsed_ms']-v['temporal_gate']['workflow_release_elapsed_ms'])
    gates['timing_ge200_ge3pairs']=len(reductions)==4 and sum(x>=200 for x in reductions)>=3
    gates['timing_median_ge200']=len(reductions)==4 and statistics.median(reductions)>=200
    h35=[s for r,s in scores if r['class']=='drop' and r.get('heading')==35]
    gates['heading35_no_extra']=len(h35)==2 and not any(s['extra_forward_issued'] for s in h35)
    wall=[s for r,s in scores if r['class']=='wall']
    gates['wall_preserves_continuation']=len(wall)==2 and all((not s['hidden_phase1_drop']) and s['extra_forward_issued'] for s in wall)
    gates['all_next_effect_release']=len(scores)==12 and all(abs(s['next_subgoal_yaw_delta'])>=5 and s['controller_release_ok'] for _,s in scores)
    gates['all_discriminator_dropped']=len(discr)==8 and all(s['hidden_phase1_drop'] for _,s in discr)
    decision='FAIL_WORKFLOW_HANDOFF'
    if not errs and all(gates.values()):decision='PASS_TEMPORAL_WORKFLOW_HANDOFF_SCOPED'
    elif not errs and (not gates['endpoint_extra_ge_3_of_4'] or not gates['timing_ge200_ge3pairs'] or not gates['timing_median_ge200']):decision='HOLD_NO_WORKFLOW_DISCRIMINATOR'
    return {'decision':decision,'errors':errs,'gates':gates,'pair_reductions_ms':reductions,'case_count':len(scores)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--schedule',required=True);p.add_argument('--freeze');p.add_argument('--out',required=True);a=p.parse_args()
    result=aggregate(a.evidence,a.schedule,a.freeze);Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()

