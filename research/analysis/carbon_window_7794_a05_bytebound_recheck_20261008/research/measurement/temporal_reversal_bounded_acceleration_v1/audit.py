from __future__ import annotations
import argparse,json
from collections import defaultdict
from common import *
EXPECTED_A0={25:.240,50:.495,75:.740,100:.995,150:1.000,200:.985}
def round_div(n,d): return (n+d//2)//d if n>=0 else -((-n+d//2)//d)
def pos_ind(t,age,post,acc):
    r=-age*1000
    if t<=r:return (-post)*(t-r)
    dt=t-r; return post*(dt+round_div(acc*dt*dt,2*100000*1_000_000))
def est_ind(obs):
    def sign(d):
        pos=abs(d-100000)<=2000; neg=abs(d+100000)<=2000
        if pos==neg:return None
        return 1 if pos else -1
    sn=sign(obs[0]-obs[1]); sp=sign(obs[1]-obs[2])
    if sn is not None:return 0 if sp==sn else sn
    if sp is not None:return -sp
    return 0
def audit(path,formal=True):
    p=json.load(open(path)); rows=p.get('rows',[]); errors=[]; exp=6000 if formal else 120
    if len(rows)!=exp or p.get('row_count')!=exp:errors.append('row_count')
    if formal and p.get('formal_invocation')!=1:errors.append('invocation')
    if p.get('reruns')!=0:errors.append('reruns')
    seen=set(); bytraj=defaultdict(set); agg=defaultdict(lambda:[0,0,0,0])
    for r in rows:
        key=(r.get('trajectory_id'),r.get('arm'))
        if key in seen:errors.append('duplicate')
        seen.add(key); bytraj[r['trajectory_id']].add(r['arm'])
        if r.get('arm') not in ACCEL_ARMS or r.get('accel_ppm_per_100ms')!=ACCEL_ARMS.get(r.get('arm')):errors.append('arm')
        if r.get('assumed_position_bound_u')!=1000:errors.append('bound')
        age=r['age_ms']; post=r['post_dir']; ts=r['sample_times_us']; acc=r['accel_ppm_per_100ms']
        exact=[pos_ind(t,age,post,acc) for t in ts]
        if exact!=r['exact_positions_u']:errors.append('exact')
        jj=[jitter_u(r['trajectory_id'],t) for t in ts]
        if jj!=r['jitter_u']:errors.append('jitter')
        obs=[x+j for x,j in zip(exact,jj)]
        if obs!=r['observed_positions_u']:errors.append('observed')
        pred=est_ind(obs)
        if pred!=r['prediction']:errors.append('prediction')
        if r['oracle']!=post:errors.append('oracle')
        if r.get('authority_granted') or r.get('task_input_granted'):errors.append('authority')
        a=agg[(r['arm'],age)]; a[0]+=1; a[1]+=int(pred==post); a[2]+=int(pred==0); a[3]+=int(pred not in (0,post))
    if any(v!=set(ACCEL_ARMS) for v in bytraj.values()):errors.append('pairing')
    metrics={}
    for (arm,age),(n,c,u,w) in agg.items():metrics.setdefault(arm,{})[age]={'n':n,'accuracy':c/n,'unknown_rate':u/n,'wrong_direction_rate':w/n}
    decision=None
    if formal and not errors:
        for age,v in EXPECTED_A0.items():
            if abs(metrics['A0'][age]['accuracy']-v)>1e-12 or metrics['A0'][age]['wrong_direction_rate']!=0:errors.append(f'a0_reproduction_{age}')
        if errors:decision='FAIL_INTEGRITY'
        else:
            wrong=any(metrics[a][age]['wrong_direction_rate']>0 for a in ACCEL_ARMS if a!='A0' for age in FORMAL_AGES_MS)
            if wrong:decision='FAIL_BOUNDED_ACCELERATION_SAFETY'
            else:
                coverage=all(metrics[a][age]['accuracy']+1e-12 >= .90*metrics['A0'][age]['accuracy'] for a in ACCEL_ARMS if a!='A0' for age in (50,75,100,150,200))
                decision='PASS_BOUNDED_ACCELERATION_REVERSAL_SAFETY_SCOPED' if coverage else 'HOLD_ACCELERATION_INCREASES_ABSTENTION'
    elif errors:decision='FAIL_INTEGRITY'
    return {'decision':decision,'errors':sorted(set(errors)),'metrics':metrics,'row_count':len(rows)}
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('path'); ap.add_argument('--construction',action='store_true'); ap.add_argument('--out'); a=ap.parse_args()
    r=audit(a.path,not a.construction); s=json.dumps(r,separators=(',',':'),sort_keys=True); print(s)
    if a.out:open(a.out,'w').write(s)
