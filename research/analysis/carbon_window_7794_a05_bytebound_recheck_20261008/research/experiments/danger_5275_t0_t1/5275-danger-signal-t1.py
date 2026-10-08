import json, random

def run(seed, fn, fp, n=1000):
    r=random.Random(seed); unsafe=detected=abstain=0; real_danger=0
    for _ in range(n):
        known=r.random()<.7; danger=r.random()<(.05 if known else .35); real_danger+=danger
        alarm=(danger and r.random()>=fn) or ((not danger) and r.random()<fp)
        if alarm: abstain+=1; detected+=int(danger)
        elif known: unsafe+=int(danger)
    return unsafe, abstain, detected, real_danger
def main():
    rows=[]
    for fn,fp in ((0,.0),(.1,.01),(.3,.05),(.5,.1),(.8,.2)):
        vals=[run(s,fn,fp) for s in range(500)]
        rows.append({'false_negative':fn,'false_positive':fp,**{k:sum(v[i] for v in vals)/len(vals) for i,k in enumerate(('unsafe_commits','abstentions','danger_detected','real_danger'))}})
    print(json.dumps({'experiment':'5275-danger-signal-t1','trials':500,'events':1000,'rows':rows,'scope':'toy noisy danger detector; no calibrated semantic oracle'},sort_keys=True,indent=2))
if __name__=='__main__': main()
