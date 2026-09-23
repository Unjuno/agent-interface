"""Frozen deterministic fixtures for Issue #4163."""
from __future__ import annotations
import numpy as np

FORMAL = [
    ("rigid_p80",416301,80,80,"rigid"),
    ("rigid_n70",416302,-70,-70,"rigid"),
    ("rigid_p165",416303,165,165,"rigid"),
    ("rigid_n175",416304,-175,-175,"rigid"),
    ("parallax_a",416305,80,180,"parallax"),
    ("parallax_b",416306,-70,-185,"parallax"),
    ("parallax_c",416307,25,170,"parallax"),
    ("parallax_d",416308,-30,150,"parallax"),
    ("unrelated",416309,None,None,"unrelated"),
    ("low_texture",416310,None,None,"low_texture"),
]

def shift_zero(a: np.ndarray, s: int) -> np.ndarray:
    out=np.full_like(a,128.0)
    if s>0: out[:,s:]=a[:,:-s]
    elif s<0: out[:,:s]=a[:,-s:]
    else: out[:]=a
    return out

def _background(seed:int)->np.ndarray:
    rng=np.random.default_rng(seed)
    a=rng.normal(0,1,(140,320))
    for _ in range(2):
        a=(a+np.roll(a,1,1)+np.roll(a,-1,1)+np.roll(a,1,0)+np.roll(a,-1,0))/5
    a=(a-a.mean())/(a.std()+1e-12)
    return np.clip(128+14*a,0,255)

def _foreground(seed:int)->np.ndarray:
    rng=np.random.default_rng(seed+10000)
    return rng.choice([15.0,240.0],size=(28,320),p=[0.5,0.5])

def scene(seed:int,bg_shift:int,fg_shift:int):
    bg=_background(seed); fg=_foreground(seed)
    ref=bg.copy(); ref[56:84]=fg
    cur=shift_zero(bg,bg_shift); cur[56:84]=shift_zero(fg,fg_shift)
    return ref,cur

def case_arrays(row):
    cid,seed,bg,fg,kind=row
    if kind in ("rigid","parallax"):
        return scene(seed,bg,fg)
    if kind=="unrelated":
        r,_=scene(seed,0,0); _,c=scene(seed+777,0,0); return r,c
    if kind=="low_texture":
        r=np.full((140,320),128.0); return r,r.copy()
    raise ValueError(kind)
