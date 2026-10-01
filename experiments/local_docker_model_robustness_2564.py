import json, time
import numpy as np

def data(n, rng, variant):
    x=rng.normal(0,.08,(n,30,40)).astype(np.float32); y=np.arange(n)%2
    for i in range(n):
        pos=bool(y[i]); cx=int(rng.integers(15,26)) if variant else 20; cy=int(rng.integers(10,21)) if variant else 15
        if pos:
            x[i,max(0,cy-3):min(30,cy+4),max(0,cx-3):min(40,cx+4)]+=.75
            if variant and i%3==0: x[i,cy-1:cy+2,cx-1:cx+2]=0
        else: x[i,2:7,2:7]+=.75
    return x.reshape(n,-1),y.astype(np.float32)

def fit(x,y,seed):
    r=np.random.default_rng(seed); a=r.normal(0,.04,(1200,12)).astype(np.float32); c=np.zeros(12,np.float32); w=r.normal(0,.04,12).astype(np.float32); b=0.
    for _ in range(300):
        h0=x@a+c; h=np.maximum(h0,0); p=1/(1+np.exp(-np.clip(h@w+b,-30,30))); dz=(p-y)/len(y)
        dw=h.T@dz; db=dz.sum(); dh=dz[:,None]*w; dh[h0<=0]=0; da=x.T@dh; dc=dh.sum(0)
        w-=.5*dw; b-=.5*db; a-=.5*da; c-=.5*dc
    return a,c,w,b

def score(m,x,y):
    a,c,w,b=m; p=1/(1+np.exp(-np.clip(np.maximum(x@a+c,0)@w+b,-30,30))); q=p>=.5
    return {'accuracy':float((q==y).mean()),'fp':int(((q==1)&(y==0)).sum()),'high_conf_pos':int((p>=.75).sum()),'n':len(y)}

def main():
    t=time.time(); rows=[]
    for seed in range(5):
        tr_x,tr_y=data(160,np.random.default_rng(100+seed),False); ev_x,ev_y=data(160,np.random.default_rng(500+seed),True)
        rows.append({'seed':seed,**score(fit(tr_x,tr_y,seed+7),ev_x,ev_y)})
    print(json.dumps({'rows':rows,'mean_accuracy':float(np.mean([r['accuracy'] for r in rows])),'min_accuracy':float(min(r['accuracy'] for r in rows)),'scope':'Docker CPU numpy model with positional shift, noise, and periodic target occlusion','seconds':time.time()-t},indent=2,sort_keys=True))
if __name__=='__main__': main()
