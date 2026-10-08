"""Docker-only local model + independent receipt/freshness gate preflight."""
import hashlib, json
import numpy as np

def sample(r, positive, shift=False):
    x=r.normal(0,.08,(30,40)).astype(np.float32); cx=24 if shift else 20; cy=15
    if positive: x[cy-3:cy+4,cx-3:cx+4]+=.75
    else: x[2:7,2:7]+=.75
    return x.reshape(-1)

def fit(x,y,seed):
    r=np.random.default_rng(seed); a=r.normal(0,.04,(1200,12)).astype(np.float32); c=np.zeros(12,np.float32); w=r.normal(0,.04,12).astype(np.float32); b=0.
    for _ in range(300):
        h0=x@a+c; h=np.maximum(h0,0); p=1/(1+np.exp(-np.clip(h@w+b,-30,30))); dz=(p-y)/len(y)
        dh=dz[:,None]*w; dh[h0<=0]=0
        a-=.5*(x.T@dh); c-=.5*dh.sum(0); w-=.5*(h.T@dz); b-=.5*dz.sum()
    return a,c,w,b

def predict(m,x):
    a,c,w,b=m; return float(1/(1+np.exp(-np.clip(np.maximum(x@a+c,0)@w+b,-30,30))))

def main():
    r=np.random.default_rng(9101)
    x=np.stack([sample(r,i%2==0) for i in range(160)]); y=1-(np.arange(160)%2); m=fit(x,y,31)
    cases=[]
    for name,positive,receipt_ok,fresh in [('known-valid',True,True,True),('known-stale',True,True,False),('receipt-mismatch',True,False,True),('negative-valid',False,True,True)]:
        p=predict(m,sample(r,positive,shift=True)); model_accept=p>=.75; final=bool(model_accept and receipt_ok and fresh)
        receipt={'saved':receipt_ok,'text':'gtk2492' if receipt_ok else 'tampered'}
        cases.append({'case':name,'model_probability':p,'model_accept':model_accept,'receipt_sha256':hashlib.sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest(),'receipt_ok':receipt_ok,'fresh':fresh,'final_accept':final})
    print(json.dumps({'cases':cases,'final_accepts':sum(c['final_accept'] for c in cases),'model_calls':4,'scope':'Docker CPU local model + independent receipt/freshness gate'},indent=2,sort_keys=True))

if __name__=='__main__': main()
