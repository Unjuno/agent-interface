"""Translate known regions by observed geometry; no visual search or authority."""
import numpy as np
from modal_visual_predicate import ModalVisualPredicate as Previous


class ModalVisualPredicate(Previous):
    def inspect_at(self,image,offset):
        a=np.asarray(image)
        if a.shape!=self.shape or a.dtype!=np.uint8:return dict(status='unsupported_frame',authority='none')
        if not isinstance(offset,(list,tuple)) or len(offset)!=2 or any(type(v)is not int for v in offset):raise ValueError('integer translation required')
        dx,dy=offset;errors=[]
        for (x,y,w,h),template in self.regions:
            x+=dx;y+=dy
            if x<0 or y<0 or x+w>a.shape[1] or y+h>a.shape[0]:return dict(status='unsupported_region',authority='none')
            errors.append(float(np.abs(a[y:y+h,x:x+w].astype(np.int16)-template).mean()/255))
        return dict(status='visual_candidate' if max(errors)<=self.max_error else 'abstain',
                    modal_error=errors[0],action_region_error=errors[1],translation=[dx,dy],
                    authority='none',semantic_verified=False)
