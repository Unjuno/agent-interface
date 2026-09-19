from pathlib import Path
import argparse, hashlib, json, statistics, sys
import cv2, numpy as np
from PIL import Image

ROI=(20,300,20,620); MIN_TRACKS=80; DY_THRESHOLD=-20.0; MAX_PAIR_DT_MS=100.0

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metric(pa,pb):
    a=np.asarray(Image.open(pa).convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    b=np.asarray(Image.open(pb).convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    ok=st[:,0]==1;p=pts[ok][:,0,:];q=p2[ok][:,0,:];d=q-p
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=int(len(d));med=None if n==0 else float(np.median(d[:,1]));status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP')
    return {'valid_tracks':n,'median_dy_px':med,'status':status}

def releases_ok(paths):
    seen=0
    for p in paths:
        if not p.exists(): continue
        rows=json.loads(p.read_text())
        for r in rows:
            if r.get('event')=='owner_release':
                seen+=1
                if not (r.get('verified') and not r.get('keys_down') and not r.get('buttons_down')): return False,seen
    return seen>0,seen

def close(a,b,tol=1e-5):
    if a is None or b is None:return a is b
    return abs(float(a)-float(b))<=tol

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',type=Path,required=True);a=ap.parse_args()
    plan=json.loads(a.plan.read_text()); root=a.root; errs=[]; rows=[]
    # source identity
    for name,expect in plan['source_sha256'].items():
        p=Path(plan['source_dir'])/name
        if not p.exists() or sha(p)!=expect: errs.append(f'source:{name}')
    if sha(plan['wad_path'])!=plan['wad_sha256']: errs.append('wad_sha')
    pos_temporal_stop=0; pos_endpoint_redundant=0; walls_ok=0
    for c in plan['cases']:
        d=root/c['id']; sp=d/'score.json'
        if not sp.exists(): errs.append(c['id']+':missing_score'); continue
        s=json.loads(sp.read_text()); p1=d/'phase1'; rp=p1/'result.json'
        if s.get('error') is not None or not rp.exists(): errs.append(c['id']+':case_error'); continue
        r=json.loads(rp.read_text()); files=[p1/x for x in r['frame_files']]
        if len(files)<8 or any(not p.exists() for p in files): errs.append(c['id']+':frames'); continue
        starts=r['frame_capture_start_ns']
        cons=[]
        for i in range(1,len(files)):
            m=metric(files[i-1],files[i]);m['dt_ms']=(starts[i]-starts[i-1])/1e6;cons.append(m)
        elig=[m for m in cons if m['dt_ms']<=MAX_PAIR_DT_MS and m['valid_tracks']>=MIN_TRACKS and m['median_dy_px'] is not None]
        temporal='DROP_COMPLETED' if any(m['median_dy_px']<=DY_THRESHOLD for m in elig) else ('UNKNOWN' if not elig else 'NO_DROP')
        endpoint=metric(files[0],files[-1])
        if temporal!=r.get('temporal_status'): errs.append(c['id']+':temporal_recompute')
        rr=r.get('endpoint',{})
        if endpoint['status']!=rr.get('status') or endpoint['valid_tracks']!=rr.get('valid_tracks') or not close(endpoint['median_dy_px'],rr.get('median_dy_px'),1e-3): errs.append(c['id']+':endpoint_recompute')
        gate_status=endpoint['status'] if c['gate']=='endpoint_gate' else temporal
        expected_extra=gate_status!='DROP_COMPLETED'
        if bool(s.get('extra_forward_issued'))!=expected_extra or bool(r.get('extra_forward_needed'))!=expected_extra: errs.append(c['id']+':gate_action')
        phase2=d/'phase2'/'owner-records.json'
        if expected_extra != phase2.exists(): errs.append(c['id']+':phase2_presence')
        ok,nrel=releases_ok([p1/'owner-records.json',phase2,d/'setup-owner-records.json'])
        if not ok: errs.append(c['id']+':release')
        hidden=bool(s.get('hidden_phase1_drop'))
        z=float(s['after_phase1']['z'])
        if hidden!=(z<=-120): errs.append(c['id']+':hidden_drop_receipt')
        if c['class']=='drop':
            if not hidden: errs.append(c['id']+':positive_not_dropped')
            if c['heading'] is None or abs(float(s['setup_alignment'].get('heading_error',999)))>=8: errs.append(c['id']+':heading')
            if c['gate']=='temporal_gate':
                if temporal!='DROP_COMPLETED' or expected_extra: errs.append(c['id']+':temporal_positive_miss')
                else: pos_temporal_stop+=1
            else:
                if hidden and expected_extra: pos_endpoint_redundant+=1
        else:
            if hidden: errs.append(c['id']+':wall_dropped')
            if endpoint['status']=='DROP_COMPLETED' or temporal=='DROP_COMPLETED' or not expected_extra: errs.append(c['id']+':wall_false_complete')
            else: walls_ok+=1
        rows.append({'id':c['id'],'seed':c['seed'],'class':c['class'],'heading':c['heading'],'gate':c['gate'],'hidden_phase1_drop':hidden,'endpoint_status':endpoint['status'],'endpoint_dy':endpoint['median_dy_px'],'temporal_status':temporal,'extra_forward_issued':expected_extra,'release_receipts':nrel})
    complete=len(rows)==len(plan['cases']) and not errs
    temporal_pos=sum(1 for c in plan['cases'] if c['class']=='drop' and c['gate']=='temporal_gate')
    endpoint_pos=sum(1 for c in plan['cases'] if c['class']=='drop' and c['gate']=='endpoint_gate')
    wall_n=sum(1 for c in plan['cases'] if c['class']=='wall')
    if not complete: decision='FAIL_INTEGRITY'
    elif pos_temporal_stop != temporal_pos or walls_ok != wall_n: decision='FAIL_TEMPORAL_COMPLETION_GATE'
    elif pos_endpoint_redundant>=2 and (pos_endpoint_redundant-(temporal_pos-pos_temporal_stop))>=2: decision='PASS_TEMPORAL_CONTINUATION_GATE_SCOPED'
    else: decision='HOLD_NO_CONTINUATION_DISCRIMINATOR'
    out={'schema':'agent-interface/map01-sector165-continuation-gate-audit-v1','status':'PASS_AUDIT' if not errs else 'FAIL_AUDIT','scientific_decision':decision,'errors':errs,'counts':{'cases':len(rows),'positive_temporal_stops':pos_temporal_stop,'positive_endpoint_redundant_continuations':pos_endpoint_redundant,'wall_correct_continuations':walls_ok},'rows':rows}
    print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if not errs else 2)
if __name__=='__main__': main()
