from pathlib import Path
import argparse,json,time,hashlib
import cv2,numpy as np
from PIL import Image
from common import Inputs,screenshot,write
ROI=(20,300,20,620); MIN_TRACKS=80; DY_THRESHOLD=-20.0; MAX_PAIR_DT_MS=100.0

def metric(a,b):
    a=np.asarray(a.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    b=np.asarray(b.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    ok=st[:,0]==1;p=pts[ok][:,0,:];q=p2[ok][:,0,:];d=q-p
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=int(len(d)); med=None if n==0 else float(np.median(d[:,1]))
    status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP')
    return {'valid_tracks':n,'median_dy_px':med,'status':status}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--ctx',required=True);p.add_argument('--pre',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);ctx=json.loads(Path(a.ctx).read_text());events=[];inp=Inputs(a.source,ctx,events)
    frames=[];starts=[];paths=[]
    def cap(tag):
        start=time.perf_counter_ns();im=screenshot(ctx['display'],ctx['geometry']);fn=out/f'{len(frames):03d}-{tag}.png';im.save(fn)
        frames.append(im);starts.append(start);paths.append(fn.name);return im
    try:
        inp.press('e',.08,.01,'task_use')
        cap('pre-forward')
        lease=inp.lease(.62);inp.owner.call('down',lease,'w');hold_start=time.perf_counter()
        try:
            while time.perf_counter()-hold_start<.45:
                cap('hold');time.sleep(.02)
        finally:
            inp.owner.call('up',lease,'w');release=inp.release(lease)
        settle_start=time.perf_counter()
        while time.perf_counter()-settle_start<.35:
            cap('settle');time.sleep(.02)
        consecutive=[]
        for i in range(1,len(frames)):
            m=metric(frames[i-1],frames[i]);m.update(i0=i-1,i1=i,dt_ms=(starts[i]-starts[i-1])/1e6);consecutive.append(m)
        eligible=[m for m in consecutive if m['dt_ms']<=MAX_PAIR_DT_MS and m['valid_tracks']>=MIN_TRACKS and m['median_dy_px'] is not None]
        temporal=any(m['median_dy_px']<=DY_THRESHOLD for m in eligible)
        endpoint=metric(frames[0],frames[-1])
        result={'schema':'agent-interface/map01-sector165-temporal-drop-controller-v1','frames':len(frames),'frame_files':paths,
                'frame_capture_start_ns':starts,'consecutive':consecutive,'eligible_pairs':len(eligible),
                'temporal_status':'DROP_COMPLETED' if temporal else ('UNKNOWN' if not eligible else 'NO_DROP'),
                'endpoint':endpoint,'min_eligible_dy_px':None if not eligible else min(m['median_dy_px'] for m in eligible),
                'max_pair_dt_ms':MAX_PAIR_DT_MS,'min_tracks':MIN_TRACKS,'threshold_dy_px':DY_THRESHOLD,
                'release':release,'controller_observation':'x11_pixels_only'}
        write(out/'result.json',result);write(out/'events.json',events);write(out/'owner-records.json',inp.owner.records)
        print(json.dumps({k:result[k] for k in ['frames','eligible_pairs','temporal_status','endpoint','min_eligible_dy_px']}))
    finally:inp.close()
if __name__=='__main__':main()
