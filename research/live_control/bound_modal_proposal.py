"""Observation-bound visual proposal. No lease, input API or authority grant."""
from dataclasses import dataclass
import hashlib
import numpy as np


@dataclass(frozen=True)
class Context:
    session: str
    sequence: int
    capture_ns: int
    window: int
    focus: int
    geometry: tuple

    def __post_init__(self):
        if not isinstance(self.session,str) or not self.session:raise ValueError('session required')
        if any(type(v)is not int or v<1 for v in (self.sequence,self.capture_ns,self.window,self.focus)):raise ValueError('positive identifiers/time required')
        if type(self.geometry)is not tuple or len(self.geometry)!=4 or any(type(v)is not int for v in self.geometry) or min(self.geometry[2:])<1:raise ValueError('immutable integer geometry required')


def digest(image):
    a=np.asarray(image)
    if a.dtype!=np.uint8 or a.ndim!=3 or a.shape[2]!=3:raise ValueError('RGB image required')
    return hashlib.sha256(str(a.shape).encode()+a.tobytes()).hexdigest()


@dataclass(frozen=True)
class BoundProposal:
    context: Context
    image_digest: str
    expires_ns: int

    def revalidate(self,current,image,now_ns):
        if type(now_ns)is not int:raise ValueError('integer clock required')
        if now_ns<self.context.capture_ns:return 'clock_before_capture'
        if now_ns>=self.expires_ns:return 'expired'
        for field in ('session','sequence','capture_ns','window','focus','geometry'):
            if getattr(current,field)!=getattr(self.context,field):return field+'_changed'
        if digest(image)!=self.image_digest:return 'pixels_changed'
        return 'requires_new_admission'


def propose(predicate,image,before,after,base_geometry,now_ns,max_age_ns=250_000_000):
    if type(max_age_ns)is not int or max_age_ns<1:raise ValueError('positive max age required')
    if type(now_ns)is not int:raise ValueError('integer clock required')
    if before!=after:return dict(status='unstable_capture',authority='none'),None
    if not before.capture_ns<=now_ns<before.capture_ns+max_age_ns:return dict(status='invalid_age',authority='none'),None
    if before.geometry[2:]!=tuple(base_geometry[2:]):return dict(status='size_changed',authority='none'),None
    offset=[before.geometry[0]-base_geometry[0],before.geometry[1]-base_geometry[1]]
    result=predicate.inspect_at(image,offset)
    if result['status']!='visual_candidate':return result,None
    return result,BoundProposal(before,digest(image),before.capture_ns+max_age_ns)
