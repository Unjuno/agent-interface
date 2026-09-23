from pathlib import Path
import argparse,json,time
import cv2,numpy as np
from PIL import Image
from common import Inputs,screenshot,write
ROI=(20,300,20,620)
MIN_TRACKS=80
DY_THRESHOLD=-20.0

def metric(pre,post):
    a=np.asarray(Image.open(pre).convert('L'),np.uint8)
    b=np.asarray(Image.open(post).convert('L'),np.uint8)
    y0,y1,x0,x1=ROI;a=a[y0:y1,x0:x1];b=b[y0:y1,x0:x1]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:
        return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:
        return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    ok=st[:,0]==1
    d=(p2[ok]-pts[ok])[:,0,:]
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100.0]
    n=int(len(d))
    med=None if not n else float(np.median(d[:,1]))
    status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP')
    return {'valid_tracks':n,'median_dy_px':med,'status':status}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--ctx',required=True);p.add_argument('--pre',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);ctx=json.loads(Path(a.ctx).read_text());events=[];inp=Inputs(a.source,ctx,events)
    try:
        inp.press('e',.08,.06,'task_use')
        inp.press('w',.45,.06,'task_forward')
        time.sleep(.35)
        post=screenshot(ctx['display'],ctx['geometry']);post.save(out/'post.png')
        result=metric(a.pre,out/'post.png')
        result.update({'schema':'agent-interface/map01-sector165-drop-controller-v1','controller_observation':'x11_pixels_only','threshold_dy_px':DY_THRESHOLD,'min_tracks':MIN_TRACKS})
        write(out/'result.json',result);write(out/'events.json',events);write(out/'owner-records.json',inp.owner.records)
        print(json.dumps(result,sort_keys=True))
    finally:inp.close()
if __name__=='__main__':main()
