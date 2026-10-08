from __future__ import annotations
import numpy as np

SUPPORT=((20,15),(8,8),(32,8),(8,22),(32,22))

def tiles(n,seed,centers,positive_size=9,negative_center=(4,4),negative_size=5,balanced=True):
    r=np.random.default_rng(seed); x=r.normal(0,.03,(n,1,30,40)).astype(np.float32); y=np.zeros(n,np.float32)
    for i in range(n):
        pos=i%2==0 if balanced else True; y[i]=float(pos)
        if pos: cx,cy=centers[(i//2)%len(centers)]; size=positive_size
        else: cx,cy=negative_center; size=negative_size
        h=size//2; x[i,0,cy-h:cy+h+1,cx-h:cx+h+1]+=.8
    return x,y

def dataset(seed):
    train=tiles(160,seed,SUPPORT)
    base=tiles(80,seed+2,((20,15),))
    held={str(c):tiles(80,seed+10+i,(c,)) for i,c in enumerate(((14,8),(26,8),(14,22),(26,22),(8,15),(20,25),(32,15),(20,8)))}
    return train,base,held
