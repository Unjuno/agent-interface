import json, random

def sample(r, n, shifted=False):
    # score is higher for positive claims; shift changes both prevalence and score separation
    for _ in range(n):
        y = r.random() < (0.5 if not shifted else 0.7)
        s = (r.gauss(.8 if y else .2, .18 if not shifted else .25))
        yield y, s

def eval_policy(rows, threshold):
    pred=[(s>=threshold,y) for y,s in rows]
    claimed=[y for p,y in pred if p]
    risk=sum(not y for y in claimed)/len(claimed) if claimed else 0
    coverage=len(claimed)/len(rows)
    return {'risk':risk,'coverage':coverage,'claims':len(claimed)}

def main():
    r=random.Random(5315); cal=list(sample(r,500)); test=list(sample(r,500)); shift=list(sample(r,500,True))
    # predeclared target empirical risk <= 0.05; quantile-like conservative threshold
    negatives=sorted(s for y,s in cal if not y); threshold=negatives[int(.95*len(negatives))]
    out={'experiment':'5315-calibration-t0','calibration_n':len(cal),'threshold':threshold,
         'fixed_threshold':.5,'iid':{'calibrated':eval_policy(test,threshold),'fixed':eval_policy(test,.5)},
         'shifted':{'calibrated':eval_policy(shift,threshold),'fixed':eval_policy(shift,.5)},
         'scope':'toy Gaussian score; split is fixed and independent; no conformal finite-sample proof or adaptive queries'}
    print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__': main()
