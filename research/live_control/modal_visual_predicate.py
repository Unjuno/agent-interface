"""Known-layout visual proposal only; no authority, action or semantic proof."""
import numpy as np


class ModalVisualPredicate:
    def __init__(self, image, modal_box, action_box, max_error=.03):
        a=np.asarray(image)
        if a.dtype!=np.uint8 or a.ndim!=3 or a.shape[2]!=3:raise ValueError('RGB uint8 required')
        if not 0<=max_error<=1:raise ValueError('invalid threshold')
        self.shape=a.shape;self.max_error=max_error;self.regions=[]
        for box in (modal_box,action_box):
            if len(box)!=4 or any(type(v)is not int for v in box):raise ValueError('integer box required')
            x,y,w,h=box
            if x<0 or y<0 or w<1 or h<1 or x+w>a.shape[1] or y+h>a.shape[0]:raise ValueError('invalid region')
            self.regions.append((tuple(box),a[y:y+h,x:x+w].astype(np.int16).copy()))

    def inspect(self,image):
        a=np.asarray(image)
        if a.shape!=self.shape or a.dtype!=np.uint8:return dict(status='unsupported_frame',authority='none')
        errors=[]
        for (x,y,w,h),template in self.regions:
            errors.append(float(np.abs(a[y:y+h,x:x+w].astype(np.int16)-template).mean()/255))
        return dict(status='visual_candidate' if max(errors)<=self.max_error else 'abstain',
                    modal_error=errors[0],action_region_error=errors[1],authority='none',
                    semantic_verified=False)
