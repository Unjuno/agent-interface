from pathlib import Path
import argparse,json,time
import cv2,numpy as np
from common import Inputs,screenshot,write
ROI=(20,300,20,620); MIN_TRACKS=80; DY_THRESHOLD=-20.0; MAX_PAIR_DT_MS=100.0

def metric(a,b):
    a=np.asarray(a.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    b=np.asarray(b.convert('L'),np.uint8)[ROI[0]:ROI[1],ROI[2]:ROI[3]]
    pts=cv2.goodFeaturesToTrack(a,maxCorners=700,qualityLevel=.01,minDistance=6,blockSize=7)
    if pts is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    p2,st,_=cv2.calcOpticalFlowPyrLK(a,b,pts,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    if p2 is None or st is None:return {'valid_tracks':0,'median_dy_px':None,'status':'UNKNOWN'}
    ok=st[:,0]==1;p=pts[ok][:,0,:];q=p2[ok][:,0,:];d=q-p
    if len(d):d=d[np.hypot(d[:,0],d[:,1])<100]
    n=int(len(d));med=None if n==0 else float(np.median(d[:,1]));status='UNKNOWN' if n<MIN_TRACKS else ('DROP_COMPLETED' if med<=DY_THRESHOLD else 'NO_DROP')
    return {'valid_tracks':n,'median_dy_px':med,'status':status}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--ctx',required=True);p.add_argument('--out',required=True);p.add_argument('--gate',choices=['endpoint_gate','temporal_gate'],required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);ctx=json.loads(Path(a.ctx).read_text());events=[];inp=Inputs(a.source,ctx,events);frames=[];starts=[];paths=[]
    def cap(tag):
        st=time.perf_counter_ns();im=screenshot(ctx['display'],ctx['geometry']);fn=out/f'{len(frames):03d}-{tag}.png';im.save(fn);frames.append(im);starts.append(st);paths.append(fn.name)
    try:
        inp.press('e',.08,.01,'task_use');cap('pre-forward')
        lease=inp.lease(.62);inp.owner.call('down',lease,'w');t0=time.perf_counter()
        try:
            while time.perf_counter()-t0<.45:cap('hold');time.sleep(.02)
        finally:
            inp.owner.call('up',lease,'w');release=inp.release(lease)
        s0=time.perf_counter()
        while time.perf_counter()-s0<.35:cap('settle');time.sleep(.02)
        consecutive=[]
        for i in range(1,len(frames)):
            m=metric(frames[i-1],frames[i]);m.update(i0=i-1,i1=i,dt_ms=(starts[i]-starts[i-1])/1e6);consecutive.append(m)
        eligible=[m for m in consecutive if m['dt_ms']<=MAX_PAIR_DT_MS and m['valid_tracks']>=MIN_TRACKS and m['median_dy_px'] is not None]
        temporal='DROP_COMPLETED' if any(m['median_dy_px']<=DY_THRESHOLD for m in eligible) else ('UNKNOWN' if not eligible else 'NO_DROP')
        endpoint=metric(frames[0],frames[-1]);complete=(endpoint['status']=='DROP_COMPLETED') if a.gate=='endpoint_gate' else (temporal=='DROP_COMPLETED')
        result={'schema':'agent-interface/map01-sector165-continuation-gate-v1','gate':a.gate,'frames':len(frames),'frame_files':paths,'frame_capture_start_ns':starts,'consecutive':consecutive,'temporal_status':temporal,'endpoint':endpoint,'extra_forward_needed':not complete,'release':release,'controller_observation':'x11_pixels_only'}
        write(out/'result.json',result);write(out/'events.json',events);write(out/'owner-records.json',inp.owner.records);print(json.dumps({'gate':a.gate,'temporal_status':temporal,'endpoint':endpoint,'extra_forward_needed':not complete}))
    finally:inp.close()
if __name__=='__main__':main()
