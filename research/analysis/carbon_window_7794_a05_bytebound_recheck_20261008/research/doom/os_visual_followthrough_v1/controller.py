"""Pixel-only follow-through: re-anchor view or resolve a target, then act.
No ViZDoom, document, scorer stream, hidden coordinates or direct app API.
"""
from pathlib import Path
import argparse,json,time,hashlib
import cv2,numpy as np
from PIL import Image
from common import Inputs,screenshot,write
from reference_controller_v3 import Matcher
cv2.setNumThreads(1)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--config',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();c=json.loads(Path(a.config).read_text());out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    ref=np.asarray(Image.open(c['reference']).convert('RGB'));matcher=Matcher(ref)
    events=[];i=0;inp=Inputs(a.source,c['context'],events);decision='UNSET';t0=time.perf_counter_ns()
    def capture():
        nonlocal i
        start=time.perf_counter_ns();im=screenshot(c['context']['display'],c['box']);end=time.perf_counter_ns()
        arr=np.asarray(im);f=f'{i:03d}.png';i+=1;im.save(out/f)
        s=time.perf_counter_ns();m=matcher.locate(arr);e=time.perf_counter_ns()
        events.append(dict(kind='observation',capture_started_ns=start,capture_ns=end,image=f,rgb_sha256=hashlib.sha256(arr.tobytes()).hexdigest(),compute_ns=e-s,match=m))
        return arr,m,end
    try:
        arr,m,cap=capture();mode=c['mode'];search=0;stable=0
        if mode in ('single','feedback','search-feedback','restore_view'):
            for j in range(1 if mode=='single' else 10):
                while not m['valid'] and mode=='search-feedback' and search<6:
                    key=['Left','Left','Right','Right','Right','Right'][search];search+=1
                    inp.press(key,.08,.14,'search');arr,m,cap=capture()
                if not m['valid']:decision='YIELD_MATCH';break
                error=m['x_error_px']
                if abs(error)<=6:
                    stable+=1
                    if stable>=2 or mode=='single':decision='ALIGNED';break
                    time.sleep(.10);arr,m,cap=capture();continue
                stable=0;key='Right' if -error/c['gain']>0 else 'Left'
                keys=['Control_L',key] if c['domain']=='inkscape' else [key]
                inp.press(keys,min(.15,max(.028,.65*abs(error/c['gain']))),.14,'reanchor');arr,m,cap=capture()
            else:decision='SINGLE_COMPLETE' if mode=='single' else 'LIMIT'
        else:decision='LOCATED' if m['valid'] else 'YIELD_MATCH'
        if c['domain']=='doom':
            # Fixed reference-scene action program, identical in both arms.
            # The single-shot comparator continues after its one correction.
            eligible=decision in ('ALIGNED','SINGLE_COMPLETE')
            events.append(dict(kind='task_gate',eligible=eligible,basis=decision))
            if eligible:
                for keys,duration in c['program']:inp.press(keys,duration,.035,'door_transit')
                capture();decision='PROGRAM_COMPLETE'
        else:
            eligible=decision in ('ALIGNED','LOCATED')
            if mode=='stale_coordinates':eligible=True
            if eligible:
                # Reobserve immediately before deriving the click; prior match grants no authority.
                point=np.asarray(c['point'],np.float32)
                if mode=='resolve_target' or mode=='restore_view':
                    if not m['valid']:decision='YIELD_MATCH';return
                    point=cv2.perspectiveTransform(point.reshape(1,1,2),np.asarray(m['homography']))[0,0]
                # Slow scene matching cannot substitute for a fresh target observation.
                start=time.perf_counter_ns();im=screenshot(c['context']['display'],c['box']);cap=time.perf_counter_ns()
                arr=np.asarray(im);f=f'{i:03d}.png';i+=1;im.save(out/f)
                events.append(dict(kind='target_observation',capture_started_ns=start,capture_ns=cap,image=f,rgb_sha256=hashlib.sha256(arr.tobytes()).hexdigest()))
                x,y=map(lambda v:int(round(float(v))),point);rx,ry=map(lambda v:int(round(float(v))),c['point']);r=5
                h,w=arr.shape[:2];same_shape=ref.shape==arr.shape
                patch_ok=same_shape and r<=x<w-r and r<=y<h-r
                diff=None
                if patch_ok:
                    rp=ref[ry-r:ry+r+1,rx-r:rx+r+1].astype(float);cp=arr[y-r:y+r+1,x-r:x+r+1].astype(float)
                    diff=float(np.max(np.abs(rp-cp)));patch_ok=diff<=8.0
                age=time.perf_counter_ns()-cap;patch_ok=patch_ok and age<=500_000_000
                events.append(dict(kind='target_gate',eligible=bool(patch_ok),target=[x,y],max_pixel_error=diff,source=c['reference'],observation_age_ns=age))
                if not patch_ok:decision='YIELD_TARGET_CHANGED';return
                inp.click(c['box'][0]+x,c['box'][1]+y)
                inp.press('Delete',purpose='delete_target');inp.press(['Control_L','s'],purpose='save_document')
                time.sleep(.25);capture();decision='PROGRAM_COMPLETE'
    except Exception as exc:
        decision='ERROR';events.append(dict(kind='error',error=repr(exc)))
    finally:
        inp.close();write(out/'trace.json',dict(decision=decision,events=events,owner_records=inp.owner.records,elapsed_ns=time.perf_counter_ns()-t0,model_calls=0))
        print(json.dumps(dict(decision=decision,observations=i)))
if __name__=='__main__':main()
