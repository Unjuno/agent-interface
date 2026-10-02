from __future__ import annotations

import numpy as np
from models import init as cnn_init, forward as conv_forward, sigmoid


def loss(model, x, y):
    p = conv_forward(x, model)
    return float(-np.mean(y*np.log(np.maximum(p, 1e-12)) + (1-y)*np.log(np.maximum(1-p, 1e-12))))


def analytical(model, x, y):
    kernel,bias,dense,out_bias=model
    windows=np.lib.stride_tricks.sliding_window_view(x[:,0],(3,3),axis=(1,2))
    pre=np.einsum("nhwij,fij->nhwf",windows,kernel,optimize=True)+bias
    act=np.maximum(pre,0)
    flat=act.reshape(len(x),-1,4); argmax=np.argmax(flat,axis=1)
    pool=np.max(flat,axis=1); p=sigmoid(pool@dense+out_bias)
    dz=(p-y)/len(y)
    ddense=np.max(flat,axis=1).T@dz; dout=dz.sum()
    dact=np.zeros_like(flat); dact[np.arange(len(x))[:,None],argmax,np.arange(4)[None,:]]=dz[:,None]*dense
    dpre=dact.reshape(pre.shape)*(pre>0)
    dk=np.einsum("nhwij,nhwf->fij",windows,dpre,optimize=True); db=dpre.sum(axis=(0,1,2))
    return dk,db,ddense,dout


def check(seed=8964300):
    rng=np.random.default_rng(seed)
    x=rng.normal(0,.2,(3,1,8,9)).astype(np.float32)
    y=np.asarray([0.,1.,1.],np.float32)
    model=tuple(np.asarray(p,dtype=np.float64) for p in cnn_init(seed+1))
    # Add nonzero bias to avoid the all-inactive ReLU initialization basin.
    model=(model[0],np.full(4,.13,np.float64),model[2],np.float64(.07))
    grads=analytical(model,x.astype(np.float64),y.astype(np.float64))
    rel=[];checked=[]
    eps=1e-5
    for family,param,grad in zip(("kernel","bias","dense","out_bias"),model,grads):
        indices=[()] if param.ndim==0 else list(np.ndindex(param.shape))
        for idx in indices:
            plus=[p.copy() for p in model];minus=[p.copy() for p in model]
            fi=("kernel","bias","dense","out_bias").index(family)
            if param.ndim==0:
                plus[fi]=np.asarray(float(param)+eps); minus[fi]=np.asarray(float(param)-eps)
            else:
                plus[fi][idx]+=eps; minus[fi][idx]-=eps
            numeric=(loss(plus,x.astype(np.float64),y.astype(np.float64))-loss(minus,x.astype(np.float64),y.astype(np.float64)))/(2*eps)
            exact=float(grad[idx]); err=abs(numeric-exact)/max(1e-6,abs(numeric)+abs(exact))
            rel.append(err);checked.append((family,idx,numeric,exact))
    maxerr=max(rel)
    return {"construction_seed":seed,"checked_parameter_values":len(rel),
            "families":{n:int(p.size) for n,p in zip(("kernel","bias","dense","out_bias"),model)},
            "max_symmetric_relative_error":maxerr,"pass":maxerr<2e-4}


if __name__=="__main__":
    import json
    print(json.dumps(check(),indent=2,sort_keys=True))

