from __future__ import annotations

import numpy as np

STEPS = 250
LR = np.float32(0.8)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def mlp_init(seed):
    rng = np.random.default_rng(seed)
    return (rng.normal(0, .04, (1200, 16)).astype(np.float32), np.zeros(16, np.float32),
            rng.normal(0, .04, 16).astype(np.float32), np.float32(0))


def mlp_fit(x, y, seed):
    w1, b1, w2, b2 = mlp_init(seed)
    for _ in range(STEPS):
        h0 = x @ w1 + b1
        h = np.maximum(h0, 0)
        p = sigmoid(h @ w2 + b2)
        dz = (p-y)/len(y)
        dw2, db2 = h.T@dz, dz.sum()
        dh = dz[:, None]*w2
        dh[h0 <= 0] = 0
        dw1, db1 = x.T@dh, dh.sum(0)
        w2 -= LR*dw2; b2 -= LR*db2; w1 -= LR*dw1; b1 -= LR*db1
    return w1, b1, w2, b2


def mlp_predict(model, x):
    w1,b1,w2,b2=model
    return sigmoid(np.maximum(x@w1+b1,0)@w2+b2)


def conv_forward(x, model, cache=False):
    kernel, bias, dense, out_bias = model
    # x[N,1,H,W], shared 3x3 valid convolution then ReLU and spatial max.
    windows = np.lib.stride_tricks.sliding_window_view(x[:, 0], (3, 3), axis=(1, 2))
    pre = np.einsum("nhwij,fij->nhwf", windows, kernel, optimize=True) + bias
    act = np.maximum(pre, 0)
    flat = act.reshape(len(x), -1, 4)
    argmax = np.argmax(flat, axis=1)
    pooled = np.max(flat, axis=1)
    z = pooled @ dense + out_bias
    if cache:
        return sigmoid(z), (windows, pre, argmax, act.shape)
    return sigmoid(z)


def cnn_init(seed):
    rng=np.random.default_rng(seed)
    return (rng.normal(0,.04,(4,3,3)).astype(np.float32), np.zeros(4,np.float32),
            rng.normal(0,.04,4).astype(np.float32), np.float32(0))


def cnn_fit(x, y, seed):
    model=list(cnn_init(seed))
    for _ in range(STEPS):
        p,(windows,pre,argmax,act_shape)=conv_forward(x,model,cache=True)
        dz=(p-y)/len(y)
        dense=model[2]; d_dense=np.max(np.maximum(pre,0).reshape(len(x),-1,4),axis=1).T@dz
        d_out=dz.sum()
        d_pool=dz[:,None]*dense[None,:]
        d_act=np.zeros(act_shape,np.float32).reshape(len(x),-1,4)
        rows=np.arange(len(x))[:,None]
        chans=np.arange(4)[None,:]
        d_act[rows,argmax,chans]=d_pool
        d_pre=d_act.reshape(act_shape)*(pre>0)
        d_kernel=np.einsum("nhwij,nhwf->fij",windows,d_pre,optimize=True)
        d_bias=d_pre.sum(axis=(0,1,2))
        model[2]-=LR*d_dense; model[3]-=LR*d_out
        model[0]-=LR*d_kernel; model[1]-=LR*d_bias
    return tuple(model)


def cnn_predict(model,x):
    return conv_forward(x,model)


def model_bytes(model):
    import io
    b=io.BytesIO()
    np.savez_compressed(b, **{f"p{i}":v for i,v in enumerate(model)})
    return b.getvalue()

