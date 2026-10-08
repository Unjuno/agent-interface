import json, random

def run(seed, mode, n=1000):
    r=random.Random(seed); safe=0; unsafe=0; abstain=0
    for _ in range(n):
        known=r.random()<.7; damage=r.random()<(.05 if known else .35)
        if mode=='identity': decision=known
        else: decision=known and damage
        if decision and not damage: unsafe+=1
        elif not decision and damage: abstain+=1
        if decision and damage: safe+=1
    return unsafe,abstain,safe
def main():
    out={m:[sum(run(s,m)[i] for s in range(200))/200 for i in range(3)] for m in ('identity','danger')}
    print(json.dumps({'experiment':'5275-danger-signal-t0','trials':200,'events':1000,'results':out,'scope':'toy known/unknown state; no calibrated detector or semantic oracle'},sort_keys=True,indent=2))
if __name__=='__main__': main()
