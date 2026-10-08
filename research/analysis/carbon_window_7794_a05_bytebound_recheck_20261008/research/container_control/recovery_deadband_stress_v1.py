import random, json, statistics, hashlib, time
from pathlib import Path
DT=0.01; WAIT=0.60; SAFE=0.55; CONTROL=1.25; DRIFT=0.95; N=700; SEED=99150916
budgets=[0.08,0.16,0.24,0.32]
noises=[0.0,0.01,0.03,0.06]
switch_probs=[0.0,0.15,0.35,0.60]
guard_disp=0.16
deadbands=[0.0,0.03,0.06,0.10,0.14]

def one(rng,budget,noise,sp,db,arm):
    x0=rng.uniform(-0.42,0.42); a_prev=-1 if x0>0 else 1
    drift_sign=1 if rng.random()<0.5 else -1
    switch_t=rng.uniform(0.06,0.42) if rng.random()<sp else None
    x=x0; unsafe=harm=held=0.0; cancelled=False
    for k in range(round(WAIT/DT)):
        t=k*DT
        if switch_t is not None and t>=switch_t: drift_sign*=-1; switch_t=None
        x_obs=x+rng.gauss(0,noise)
        active=False
        if arm=='recovery' and t<budget and not cancelled:
            direction_ok=((x_obs>=0 and a_prev==-1) or (x_obs<0 and a_prev==1))
            disp_ok=abs(x_obs-x0)<=guard_disp
            deadband_ok=abs(x_obs)>=db
            if direction_ok and disp_ok and deadband_ok: active=True
            else: cancelled=True
        u=CONTROL*a_prev if active else 0.0
        x_before=x
        noinput_x=x_before + DRIFT*drift_sign*DT
        x=x_before + (DRIFT*drift_sign+u)*DT
        if active: held+=DT
        if abs(x)>SAFE: unsafe+=DT
        if active and abs(x)>abs(noinput_x)+1e-12: harm+=DT
    return unsafe,harm,held,cancelled

def cond(b,n,sp,db):
    ds=[]; harms=[]; held=[]; canc=[]
    for i in range(N):
        s=SEED+i*1000003+int(b*1000)*97+int(n*1000)*193+int(sp*100)*389+int(db*1000)*991
        c=one(random.Random(s),b,n,sp,db,'coast')
        r=one(random.Random(s),b,n,sp,db,'recovery')
        ds.append(r[0]-c[0]); harms.append(r[1]); held.append(r[2]); canc.append(r[3])
    return {'budget_s':b,'noise':n,'switch_prob':sp,'deadband':db,'n':N,
      'mean_delta_unsafe_s':statistics.fmean(ds),'median_delta_unsafe_s':statistics.median(ds),
      'better_rate':sum(d<0 for d in ds)/N,'worse_rate':sum(d>0 for d in ds)/N,
      'harm_episode_rate':sum(h>0 for h in harms)/N,'median_held_s':statistics.median(held),'cancel_rate':sum(canc)/N}

rows=[]; t=time.perf_counter()
for b in budgets:
 for n in noises:
  for sp in switch_probs:
   for db in deadbands: rows.append(cond(b,n,sp,db))
base={(r['budget_s'],r['noise'],r['switch_prob']):r for r in rows if r['deadband']==0.0}
compar=[]
for r in rows:
 if r['deadband']==0: continue
 q=base[(r['budget_s'],r['noise'],r['switch_prob'])]
 compar.append({**r,'worse_rate_change':r['worse_rate']-q['worse_rate'],'harm_rate_change':r['harm_episode_rate']-q['harm_episode_rate'],'mean_delta_change':r['mean_delta_unsafe_s']-q['mean_delta_unsafe_s']})
agg=[]
for b in budgets:
 for n in noises:
  for db in deadbands[1:]:
   rr=[r for r in rows if r['budget_s']==b and r['noise']==n and r['deadband']==db]
   agg.append({'budget_s':b,'noise':n,'deadband':db,'max_worse_rate':max(x['worse_rate'] for x in rr),'max_harm_episode_rate':max(x['harm_episode_rate'] for x in rr),'worst_mean_delta_unsafe_s':max(x['mean_delta_unsafe_s'] for x in rr),'best_mean_delta_unsafe_s':min(x['mean_delta_unsafe_s'] for x in rr),'min_median_held_s':min(x['median_held_s'] for x in rr)})
robust=sorted([a for a in agg if a['max_worse_rate']<=0.02 and a['worst_mean_delta_unsafe_s']<=0], key=lambda a:(a['max_worse_rate'],a['worst_mean_delta_unsafe_s']))
best_changes=sorted(compar,key=lambda x:(x['worse_rate_change'],x['harm_rate_change']))[:10]
out={'schema':'bounded-recovery-deadband-stress-v1','seed':SEED,'n_per_condition':N,'conditions':len(rows),'runtime_s':time.perf_counter()-t,'robust':robust,'best_changes':best_changes,'rows':rows}
raw=json.dumps(out,sort_keys=True,separators=(',',':')).encode(); out['sha256_without_sha_field']=hashlib.sha256(raw).hexdigest()
Path('/tmp/recovery_deadband_stress_v1.json').write_text(json.dumps(out,indent=2,sort_keys=True))
print('runtime',out['runtime_s'],'conditions',len(rows),'episodes',len(rows)*N)
print('ROBUST',len(robust))
for x in robust[:12]: print(x)
print('BEST_CHANGES')
for x in best_changes[:5]: print(x)
