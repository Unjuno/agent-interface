from __future__ import annotations
import numpy as np
from PIL import Image
ROI=(160,120,480,260)
SEARCH_PX=160
SHIFT_STOP_PX=34
MAE_STOP=0.035

def _arr(path):
    return np.asarray(Image.open(path).convert('RGB'),dtype=np.float32)

def normalized_mae(ref_path,cur_path):
    a=_arr(ref_path); b=_arr(cur_path); x0,y0,x1,y1=ROI
    if a.shape!=b.shape or a.shape[:2]!=(480,640): raise ValueError('exact 640x480 RGB source required')
    return float(np.abs(a[y0:y1,x0:x1]-b[y0:y1,x0:x1]).mean()/255.0)

def horizontal_shift(ref_path,cur_path):
    a=_arr(ref_path); b=_arr(cur_path); x0,y0,x1,y1=ROI
    if a.shape!=b.shape or a.shape[:2]!=(480,640): raise ValueError('exact 640x480 RGB source required')
    def grad(z):
        r=z[y0:y1,x0:x1]
        lum=.299*r[:,:,0]+.587*r[:,:,1]+.114*r[:,:,2]
        return np.diff(lum,axis=1)
    A=grad(a); B=grad(b)
    if float(A.std())<2 or float(B.std())<2: return {'status':'UNKNOWN_FLAT','shift_px':None,'corr':None,'margin':None}
    vals=[]; w=A.shape[1]
    for s in range(-SEARCH_PX,SEARCH_PX+1):
        if s<0: aa=A[:,:w+s]; bb=B[:,-s:]
        elif s>0: aa=A[:,s:]; bb=B[:,:w-s]
        else: aa=A; bb=B
        av=aa.ravel().astype(np.float64); bv=bb.ravel().astype(np.float64)
        av-=av.mean(); bv-=bv.mean(); den=np.sqrt(np.dot(av,av)*np.dot(bv,bv))
        vals.append((float(np.dot(av,bv)/den) if den else -1.0,s))
    vals.sort(reverse=True); corr,s=vals[0]
    second=max((c for c,t in vals if abs(t-s)>4),default=-1.0)
    if abs(s)==SEARCH_PX: status='UNKNOWN_BOUNDARY'
    else: status='MATCHED' if abs(s)<=SHIFT_STOP_PX else 'CONTINUE'
    return {'status':status,'shift_px':int(s),'corr':corr,'margin':corr-second}

def decide(arm,ref_path,cur_path):
    if ref_path is None: return {'status':'UNKNOWN_MISSING_REFERENCE'}
    if arm=='RGB_MAE_STOP':
        v=normalized_mae(ref_path,cur_path)
        return {'status':'MATCHED' if v<=MAE_STOP else 'CONTINUE','mae':v,'threshold':MAE_STOP}
    if arm=='HORIZONTAL_SHIFT_STOP':
        return horizontal_shift(ref_path,cur_path)
    raise ValueError('unknown arm')
