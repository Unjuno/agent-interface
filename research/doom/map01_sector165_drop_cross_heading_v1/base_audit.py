from pathlib import Path
import argparse,hashlib,json,sys
import cv2,numpy as np
from PIL import Image
ROI=(20,300,20,620);MIN_TRACKS=80;DY_THRESHOLD=-20.0

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metric(pre,post):
    a=np.asarray(Image.open(pre).convert('L'),np.uint8);b=np.asarray(Image.open(post).convert('L'),np.uint8);y0,y1,x0,x1=ROI;a=a[y0:y1,x0:x1];b=b[y0:y1,x0:x1]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:return 0,None,'UNKNOWN'
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:return 0,None,'UNKNOWN'
    d=(p2[st[:,0]==1]-pts[st[:,0]==1])[:,0,:];d=d[np.hypot(d[:,0],d[:,1])<100.0] if len(d) else d;n=len(d);med=None if not n else float(np.median(d[:,1]));status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP');return int(n),med,status

def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--plan',required=True);p.add_argument('--prereg',required=True);a=p.parse_args();root=Path(a.root);plan=json.loads(Path(a.plan).read_text());pre=json.loads(Path(a.prereg).read_text());errors=[];rows=[]
    for name,h in pre['source_sha256'].items():
        if sha(Path(a.prereg).parent/name)!=h:errors.append('source_hash:'+name)
    for c in plan['cases']:
        d=root/c['id']
        try:
            s=json.loads((d/'score.json').read_text());cr=json.loads((d/'controller/result.json').read_text());n,med,status=metric(d/'pre.png',d/'controller/post.png');owners=json.loads((d/'controller/owner-records.json').read_text());rel=all(r.get('verified') and not r.get('keys_down') and not r.get('buttons_down') for r in owners if r.get('event')=='owner_release')
            if s.get('error') is not None or s.get('controller_returncode')!=0:errors.append(c['id']+':case_error')
            if (n,med,status)!=(cr.get('valid_tracks'),cr.get('median_dy_px'),cr.get('status')):errors.append(c['id']+':metric')
            if not rel or not s.get('setup_release_ok'):errors.append(c['id']+':release')
            hidden=s.get('hidden_effect');expected='DROP' if c['class']=='drop' else 'NO_DROP'
            if hidden!=expected:errors.append(c['id']+':fixture_effect')
            if c['class']=='drop' and status!='DROP_COMPLETED':errors.append(c['id']+':drop_missed')
            if c['class']=='wall' and status=='DROP_COMPLETED':errors.append(c['id']+':false_drop')
            rows.append({'id':c['id'],'class':c['class'],'seed':c['seed'],'valid_tracks':n,'median_dy_px':med,'pixel_status':status,'hidden_effect':hidden,'release_ok':rel})
        except Exception as e:errors.append(c['id']+':'+repr(e))
    pos=[r for r in rows if r['class']=='drop'];neg=[r for r in rows if r['class']=='wall']
    if errors:decision='FAIL_INTEGRITY_OR_EFFECT'
    elif len(pos)==4 and all(r['pixel_status']=='DROP_COMPLETED' for r in pos) and len(neg)==4 and all(r['pixel_status']!='DROP_COMPLETED' for r in neg):decision='PASS_PIXEL_DROP_EFFECT_SCOPED'
    elif any(r['pixel_status']=='DROP_COMPLETED' for r in neg):decision='FAIL_FALSE_DROP_EFFECT'
    else:decision='HOLD_DROP_EFFECT_NOT_OBSERVABLE'
    out={'schema':'agent-interface/map01-sector165-drop-audit-v1','status':'PASS_AUDIT' if not errors else 'FAIL_AUDIT','scientific_decision':decision,'errors':errors,'rows':rows};print(json.dumps(out,indent=2,sort_keys=True));sys.exit(0 if not errors else 2)
if __name__=='__main__':main()
