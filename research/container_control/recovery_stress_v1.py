import random, math, json, statistics, hashlib, time
from pathlib import Path

DT=0.01
WAIT=0.60
SAFE=0.55
CONTROL=1.25
DRIFT=0.95
N=1200
SEED=99150915
budgets=[0.08,0.16,0.24,0.32,0.40]
noises=[0.0,0.01,0.03,0.06]
switch_probs=[0.0,0.15,0.35,0.60]
guard_disps=[0.08,0.16,0.24]

def one(rng,budget,noise,sp,gdisp,arm):
    x0=rng.uniform(-0.42,0.42)
    a_prev=-1 if x0>0 else 1
    drift_sign=1 if rng.random()<0.5 else -1
    switch_t=rng.uniform(0.06,0.42) if rng.random()<sp else None
    x=x0; unsafe=0.0; harm=0.0; held=0.0; cancelled=False; stale_press=False
    t=0.0
    while t < WAIT-1e-12:
        if switch_t is not None and t>=switch_t: drift_sign*=-1; switch_t=None
        x_obs=x+rng.gauss(0,noise)
        active=False
        if arm=='recovery' and t<budget and not cancelled:
            directional=(x_obs==0) or ((-1 if x_obs>0 else 1)==a_prev)
            disp=abs(x_obs-x0)<=gdisp
            if directional and disp:
                active=True
            else:
                cancelled=True
        u=(CONTROL*a_prev) if active else 0.0
        before=abs(x)
        x += (DRIFT*drift_sign + u)*DT
        after=abs(x)
        if active: held += DT
        if abs(x)>SAFE: unsafe+=DT
        noinput_after=abs((x - u*DT))
        if active and after > noinput_after+1e-12: harm+=DT
        t+=DT
    return {'unsafe':unsafe,'held':held,'harm':harm,'cancelled':cancelled,'final_abs':abs(x)}

def matched_condition(budget,noise,sp,gdisp):
    coast=[]; rec=[]
    for i in range(N):
        s=(SEED + i*1000003 + int(budget*1000)*97 + int(noise*1000)*193 + int(sp*100)*389 + int(gdisp*1000)*769)
        r1=random.Random(s); r2=random.Random(s)
        coast.append(one(r1,budget,noise,sp,gdisp,'coast'))
        rec.append(one(r2,budget,noise,sp,gdisp,'recovery'))
    du=[r['unsafe']-c['unsafe'] for c,r in zip(coast,rec)]
    dh=[r['harm'] for r in rec]
    return {
      'budget_s':budget,'noise':noise,'switch_prob':sp,'guard_disp':gdisp,'n':N,
      'median_delta_unsafe_s':statistics.median(du),
      'mean_delta_unsafe_s':statistics.fmean(du),
      'recovery_better_rate':sum(d< -1e-12 for d in du)/N,
      'recovery_worse_rate':sum(d> 1e-12 for d in du)/N,
      'equal_rate':sum(abs(d)<=1e-12 for d in du)/N,
      'harm_episode_rate':sum(h>0 for h in dh)/N,
      'median_held_s':statistics.median(r['held'] for r in rec),
      'cancel_rate':sum(r['cancelled'] for r in rec)/N,
      'coast_median_unsafe_s':statistics.median(c['unsafe'] for c in coast),
      'recovery_median_unsafe_s':statistics.median(r['unsafe'] for r in rec),
    }

rows=[]
t0=time.perf_counter()
for b in budgets:
  for n in noises:
    for sp in switch_probs:
      for gd in guard_disps:
        rows.append(matched_condition(b,n,sp,gd))

safe=[r for r in rows if r['recovery_worse_rate']==0 and r['harm_episode_rate']<=0.01 and r['recovery_better_rate']>=0.5]
unsafe=sorted(rows,key=lambda r:(r['recovery_worse_rate'],r['harm_episode_rate'],r['mean_delta_unsafe_s']),reverse=True)
best=sorted(safe,key=lambda r:r['mean_delta_unsafe_s'])[:10]
robust=[r for r in rows if r['switch_prob']>=0.35 and r['noise']>=0.03 and r['recovery_worse_rate']<=0.01 and r['median_delta_unsafe_s']<=0]
robust=sorted(robust,key=lambda r:(r['recovery_worse_rate'], r['mean_delta_unsafe_s']))[:10]
out={'schema':'bounded-recovery-adversarial-stress-v1','seed':SEED,'dt_s':DT,'planner_wait_s':WAIT,'safe_abs':SAFE,'control':CONTROL,'drift':DRIFT,'episodes_per_condition':N,'conditions':len(rows),'runtime_s':time.perf_counter()-t0,'best_safeish':best,'worst_counterexamples':unsafe[:10],'robust_candidates':robust,'rows':rows}
raw=json.dumps(out,sort_keys=True,separators=(',',':')).encode()
out['sha256_without_sha_field']=hashlib.sha256(raw).hexdigest()
Path('/tmp/recovery_stress_v1.json').write_text(json.dumps(out,indent=2,sort_keys=True))
print(json.dumps({k:out[k] for k in ['schema','episodes_per_condition','conditions','runtime_s','sha256_without_sha_field']},indent=2))
print('BEST_SAFEISH')
for x in best[:5]: print(x)
print('WORST')
for x in unsafe[:5]: print(x)
print('ROBUST')
for x in robust[:5]: print(x)
