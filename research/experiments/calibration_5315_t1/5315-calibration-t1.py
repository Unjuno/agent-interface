import json, random

def rows(r,n,mode):
    for _ in range(n):
        y=r.random()<.5
        if mode=='iid': mu=.8 if y else .2
        elif mode=='prevalence': mu=.8 if y else .2
        else: mu=.2 if y else .8 # adverse score inversion
        yield y,r.gauss(mu,.18)
def evaluate(rs,t):
    claims=[y for y,s in rs if s>=t]
    return {'risk':sum(not y for y in claims)/len(claims) if claims else 0,'coverage':len(claims)/len(rs)}
def main():
    allout=[]
    for seed in range(100):
        r=random.Random(seed); cal=list(rows(r,500,'iid')); neg=sorted(s for y,s in cal if not y); t=neg[int(.95*len(neg))]
        a=list(rows(r,500,'iid')); b=list(rows(r,500,'prevalence')); c=list(rows(r,500,'adverse'))
        allout.append({'seed':seed,'threshold':t,'iid':evaluate(a,t),'prevalence':evaluate(b,t),'adverse':evaluate(c,t)})
    def mean(k,p): return sum(x[p][k] for x in allout)/len(allout)
    print(json.dumps({'experiment':'5315-calibration-t1','seeds':100,'calibration_n':500,'test_n':500,'mean':{p:{k:mean(k,p) for k in ('risk','coverage')} for p in ('iid','prevalence','adverse')},'scope':'toy adverse score shift; no shift detector, conformal proof, or semantic oracle'},sort_keys=True,indent=2))
if __name__=='__main__': main()
