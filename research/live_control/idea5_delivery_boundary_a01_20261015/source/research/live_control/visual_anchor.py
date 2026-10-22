"""Experimental immutable RGB patch anchor; no input authority or task oracle."""
import hashlib
import numpy as np

class VisualAnchor:
    def __init__(self, image, box, observation_id, frame_id, radius=32,
                 max_error=0.03, min_margin=0.005, tolerance=2):
        a=np.asarray(image)
        if a.dtype!=np.uint8 or a.ndim!=3 or a.shape[2]!=3:raise ValueError('RGB uint8 required')
        if len(box)!=4 or any(type(v)is not int for v in box):raise ValueError('integer box required')
        x,y,w,h=box
        if min(w,h)<4 or max(w,h)>96 or x<0 or y<0 or x+w>a.shape[1] or y+h>a.shape[0]:raise ValueError('invalid patch')
        if type(radius)is not int or not 1<=radius<=64:raise ValueError('radius 1..64 required')
        if not 0<=max_error<=1 or not 0<min_margin<=1 or type(tolerance)is not int or not 0<=tolerance<radius:raise ValueError('invalid thresholds')
        self.patch=a[y:y+h,x:x+w].astype(np.int16).copy()
        if self.patch.std(axis=(0,1)).max()<8:raise ValueError('spatially flat patch')
        self.box=tuple(box);self.shape=a.shape;self.radius=radius
        self.max_error=max_error;self.min_margin=min_margin;self.tolerance=tolerance
        self.observation_id=observation_id;self.frame_id=frame_id
        self.digest=hashlib.sha256(self.patch.tobytes()).hexdigest()

    def locate(self,image,observation_id,frame_id):
        a=np.asarray(image)
        if frame_id!=self.frame_id or a.shape!=self.shape:return {'status':'invalid_frame'}
        if a.dtype!=np.uint8:return {'status':'invalid_frame'}
        if observation_id==self.observation_id:return {'status':'same_observation'}
        x,y,w,h=self.box;r=self.radius;cost=[]
        for yy in range(max(0,y-r),min(a.shape[0]-h,y+r)+1):
            for xx in range(max(0,x-r),min(a.shape[1]-w,x+r)+1):
                error=float(np.abs(a[yy:yy+h,xx:xx+w].astype(np.int16)-self.patch).mean()/255)
                cost.append((error,xx,yy))
        cost.sort();best,xx,yy=cost[0]
        rivals=[v[0] for v in cost if max(abs(v[1]-xx),abs(v[2]-yy))>self.tolerance]
        margin=min(rivals)-best if rivals else 1.0
        status='lost' if best>self.max_error else 'ambiguous' if margin<self.min_margin else 'matched'
        result={'status':status,'error':best,'margin':margin,'source_observation':self.observation_id,
                'observation':observation_id,'frame_id':frame_id,'patch_sha256':self.digest}
        if status=='matched':result.update(box=[xx,yy,w,h],delta=[xx-x,yy-y])
        return result
