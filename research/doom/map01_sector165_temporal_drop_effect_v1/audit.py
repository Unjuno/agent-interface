from pathlib import Path
import argparse,hashlib,json,sys
import cv2,numpy as np
from PIL import Image
ROI=(20,300,20,620);MIN_TRACKS=80;DY_THRESHOLD=-20.0;MAX_PAIR_DT_MS=100.0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metric(pa,pb):
    a=np.asarray(Image.open(pa).convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]];b=np.asarray(Image.open(pb).convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:return 0,None,'UNKNOWN'
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:return 0,None,'UNKNOWN'
    ok=st[:,0]==1;p=pts[ok][:,0,:];q=p2[ok][:,0,:];d=q-p
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=len(d);med=None if not n else float(np.median(d[:,1]));status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP');return int(n),med,status

def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--plan',required=True);p.add_argument('--prereg',required=True);a=p.parse_args();root=Path(a.root);plan=json.loads(Path(a.plan).read_text());pre=json.loads(Path(a.prereg).read_text());errors=[];rows=[]
    for name,h in pre['source_sha256'].items():
        if sha(Path(a.prereg).parent/name)!=h:errors.append('source_hash:'+name)
    for c in plan['cases']:
        d=root/c['id'];score=json.loads((d/'score.json').read_text());cr=json.loads((d/'controller/result.json').read_text());files=cr['frame_files'];starts=cr['frame_capture_start_ns']
        if len(files)!=len(starts) or len(files)<8:errors.append(c['id']+':frame_count');continue
        cons=[]
        for i in range(1,len(files)):
            n,dy,status=metric(d/'controller'/files[i-1],d/'controller'/files[i]);dt=(starts[i]-starts[i-1])/1e6;cons.append((n,dy,status,dt))
        elig=[x for x in cons if x[3]<=MAX_PAIR_DT_MS and x[0]>=MIN_TRACKS and x[1] is not None]
        temporal='DROP_COMPLETED' if any(x[1]<=DY_THRESHOLD for x in elig) else ('UNKNOWN' if not elig else 'NO_DROP')
        n,dy,endpoint=metric(d/'controller'/files[0],d/'controller'/files[-1])
        if temporal!=cr['temporal_status'] or endpoint!=cr['endpoint']['status']:errors.append(c['id']+':controller_metric')
        if len(elig)<6:errors.append(c['id']+':sampling')
        rel=json.loads((d/'controller/owner-records.json').read_text());release=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in rel if r.get('event')=='owner_release')
        if not release or not score.get('setup_release_ok'):errors.append(c['id']+':release')
        hidden=score.get('hidden_effect');expected='DROP' if c['class']=='drop' else 'NO_DROP'
        if hidden!=expected:errors.append(c['id']+':hidden_effect')
        rows.append({'id':c['id'],'class':c['class'],'seed':c['seed'],'heading':c.get('heading'),'hidden_effect':hidden,'temporal_status':temporal,'endpoint_status':endpoint,'eligible_pairs':len(elig),'min_temporal_dy_px':None if not elig else min(x[1] for x in elig),'endpoint_dy_px':dy,'release_ok':release})
    pos=[r for r in rows if r['class']=='drop'];walls=[r for r in rows if r['class']=='wall'];td=sum(r['temporal_status']=='DROP_COMPLETED' for r in pos);ed=sum(r['endpoint_status']=='DROP_COMPLETED' for r in pos);fp=sum(r['temporal_status']=='DROP_COMPLETED' for r in walls)
    if errors:decision='FAIL_INTEGRITY'
    elif fp:decision='FAIL_FALSE_TEMPORAL_DROP_EFFECT'
    elif len(pos)==6 and td==6 and td-ed>=2:decision='PASS_TEMPORAL_DROP_EFFECT_SCOPED'
    elif len(pos)==6 and td==6:decision='HOLD_TEMPORAL_NO_CLEAR_ADVANTAGE'
    else:decision='HOLD_TEMPORAL_DROP_MISSED'
    out={'schema':'agent-interface/map01-sector165-temporal-drop-audit-v1','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','scientific_decision':decision,'errors':errors,'temporal_positive_detections':td,'endpoint_positive_detections':ed,'wall_false_positives':fp,'rows':rows};print(json.dumps(out,indent=2,sort_keys=True));sys.exit(0 if not errors else 2)
if __name__=='__main__':main()
