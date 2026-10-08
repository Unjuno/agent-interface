"""Pixel-only reference re-anchoring. No ViZDoom import, map or game variable."""
from __future__ import annotations
import argparse,json,sys,time,hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageGrab
from Xlib import display

cv2.setNumThreads(1)
class Matcher:
    def __init__(self, reference):
        self.reference=reference
        self.sift=cv2.SIFT_create(nfeatures=1000)
        self.k,self.d=self.sift.detectAndCompute(cv2.cvtColor(reference,cv2.COLOR_RGB2GRAY),self.mask(reference))
        self.bf=cv2.BFMatcher()
    def mask(self,image):
        h,w=image.shape[:2];m=np.ones((h,w),np.uint8)*255
        m[int(.8*h):,:]=0
        m[int(.62*h):,int(.3*w):int(.7*w)]=0
        return m
    def locate(self,image):
        k,d=self.sift.detectAndCompute(cv2.cvtColor(image,cv2.COLOR_RGB2GRAY),self.mask(image))
        if self.d is None or d is None:return {'valid':False,'reason':'no_descriptors'}
        matches=[a for pair in self.bf.knnMatch(self.d,d,k=2) if len(pair)==2 for a,b in [pair] if a.distance<.70*b.distance]
        if len(matches)<12:return {'valid':False,'reason':'too_few_matches','matches':len(matches)}
        src=np.float32([self.k[a.queryIdx].pt for a in matches]);dst=np.float32([k[a.trainIdx].pt for a in matches])
        mat,inliers=cv2.findHomography(src,dst,cv2.RANSAC,3.0,maxIters=1000)
        if mat is None:return {'valid':False,'reason':'no_homography'}
        ii=inliers.ravel().astype(bool);n=int(ii.sum());span=np.ptp(src[ii],axis=0)
        if n<10 or n/len(matches)<.45 or float(span[0])<100 or float(span[1])<55:
            return {'valid':False,'reason':'weak_geometry','matches':len(matches),'inliers':n}
        h,w=image.shape[:2];point=np.float32([[[w/2,h*.40]]]);mapped=cv2.perspectiveTransform(point,mat)[0,0]
        if not np.isfinite(mapped).all() or not(-w/2<float(mapped[0])<1.5*w) or abs(float(mapped[1])-h*.40)>h*.25:
            return {'valid':False,'reason':'implausible_projection'}
        return {'valid':True,'x_error_px':float(mapped[0]-w/2),'y_error_px':float(mapped[1]-h*.40),'matches':len(matches),'inliers':n,'homography':mat.tolist()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--reference',required=True);p.add_argument('--display',required=True);p.add_argument('--focus',type=int,required=True);p.add_argument('--box',type=int,nargs=4,required=True);p.add_argument('--mode',choices=['single','feedback','search-feedback','calibrate'],required=True);p.add_argument('--modifier',default='');p.add_argument('--gain',type=float,default=-250.0);p.add_argument('--out',required=True)
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(Path(args.source)/'research/live_control'))
    from input_owner_v10 import InputOwner
    from lease import Lease
    reference=np.asarray(Image.open(args.reference).convert('RGB'));matcher=Matcher(reference)
    owner=InputOwner(args.display);d=display.Display(args.display);events=[];index=0;decision='LIMIT';x,y,w,h=args.box
    def capture():
        nonlocal index
        a=time.perf_counter_ns();im=ImageGrab.grab(xdisplay=args.display).convert('RGB').crop((x,y,x+w,y+h));b=time.perf_counter_ns()
        filename=f'{index:03d}.png';im.save(out/filename);index+=1
        arr=np.asarray(im);c=time.perf_counter_ns();m=matcher.locate(arr);e=time.perf_counter_ns()
        events.append({'kind':'observation','capture_started_ns':a,'capture_ns':b,'compute_ns':e-c,'image':filename,'rgb_sha256':hashlib.sha256(arr.tobytes()).hexdigest(),'match':m});return m
    def press(key,duration):
        if d.get_input_focus().focus.id!=args.focus:raise RuntimeError('focus_changed')
        lease=Lease(time.perf_counter_ns()+int((duration+.15)*1e9));lease.expected_focus=args.focus
        try:
            
            if args.modifier:owner.call('down',lease,args.modifier)
            receipt=owner.call('down',lease,key);time.sleep(duration)
        finally:
            up_started=time.perf_counter_ns();owner.call('up',lease,key)
            if args.modifier:owner.call('up',lease,args.modifier)
            released=owner.call('release',lease)
            events.append({'kind':'input','key':key,'requested_seconds':duration,'down':receipt,'up_started_ns':up_started,'release':released})
            if not released['verified']:raise RuntimeError('release_unverified')
        time.sleep(.14)
    try:
        m=capture()
        if args.mode=='calibrate':
            press('Right',.085);m2=capture()
            gain=(m2['x_error_px']-m['x_error_px'])/.085 if m['valid'] and m2['valid'] else None
            events.append({'kind':'calibration','gain_px_per_second':gain});decision='CALIBRATED' if gain is not None and abs(gain)>20 else 'YIELD'
        else:
            stable=0
            search_keys=iter(['Left','Left','Right','Right','Right','Right'])
            search_count=0
            for j in range(1 if args.mode=='single' else 10):
                while not m['valid'] and args.mode=='search-feedback' and search_count<6:
                    key=next(search_keys);search_count+=1
                    events.append({'kind':'bounded_search','index':search_count,'key':key,'max_search_pulses':6,'seconds':.08,'reason':m['reason']})
                    press(key,.08);m=capture()
                if not m['valid']:decision='YIELD';break
                error=m['x_error_px']
                if abs(error)<=6:
                    stable+=1
                    if stable>=2 or args.mode=='single':decision='ALIGNED';break
                    time.sleep(.10);m=capture();continue
                stable=0
                key='Right' if -error/args.gain>0 else 'Left'
                duration=min(.15,max(.028,.65*abs(error/args.gain)))
                press(key,duration);m=capture()
            else:decision='SINGLE_COMPLETE' if args.mode=='single' else 'LIMIT'
    except Exception as exc:
        decision='ERROR';events.append({'kind':'error','detail':repr(exc)})
    finally:
        owner.close();d.close()
        result={'mode':args.mode,'decision':decision,'events':events,'owner_records':owner.records,'all_release_verified':all(r.get('verified') is True for r in owner.records if r['event']=='owner_release')}
        (out/'trace.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':decision,'observations':index}))
if __name__=='__main__':main()
