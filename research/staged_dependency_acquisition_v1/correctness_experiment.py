import json, random, statistics, time, hashlib, platform
from pathlib import Path

SEED=202609160224
N=100_000
rng=random.Random(SEED)

def pick(pool, lo, hi):
    k=rng.randint(lo, min(hi,len(pool)))
    return set(rng.sample(pool,k))

rows=[]
metrics={m:{'stale_accept':0,'false_reject':0,'correct_reject':0,'correct_continue':0,'deps':[]} for m in ['state_union','staged','planner_only']}
start=time.perf_counter_ns()
for i in range(N):
    branch={'mode'}
    pending=pick([f'effect{j}' for j in range(4)],0,2)
    verifier=pick([f'verify{j}' for j in range(4)],0,2) if pending else set()
    a_symbol=pick([f'symA{j}' for j in range(4)],1,2)
    b_symbol=pick([f'symB{j}' for j in range(4)],1,2)
    a_admit=pick([f'admA{j}' for j in range(5)],1,3)
    b_admit=pick([f'admB{j}' for j in range(5)],1,3)
    selected='A' if rng.getrandbits(1)==0 else 'B'
    selected_symbol=a_symbol if selected=='A' else b_symbol
    selected_admit=a_admit if selected=='A' else b_admit
    inactive_symbol=b_symbol if selected=='A' else a_symbol
    inactive_admit=b_admit if selected=='A' else a_admit
    required=branch|pending|verifier|selected_symbol|selected_admit
    inactive=inactive_symbol|inactive_admit
    state_union=required|inactive
    staged=required
    planner_only=branch|pending|selected_symbol
    candidates={'state_union':state_union,'staged':staged,'planner_only':planner_only}
    category=rng.choice(['relevant','inactive','unrelated'])
    if category=='relevant':
        changed=rng.choice(sorted(required))
    elif category=='inactive' and inactive:
        changed=rng.choice(sorted(inactive))
    else:
        category='unrelated'; changed='unrelated'+str(rng.randrange(1000))
    truth_reject=changed in required
    for name,deps in candidates.items():
        reject=changed in deps
        if truth_reject and not reject: metrics[name]['stale_accept']+=1
        elif (not truth_reject) and reject: metrics[name]['false_reject']+=1
        elif truth_reject: metrics[name]['correct_reject']+=1
        else: metrics[name]['correct_continue']+=1
        metrics[name]['deps'].append(len(deps))
    if i<200:
        rows.append({'i':i,'selected':selected,'category':category,'changed':changed,
                     'required':sorted(required),'inactive':sorted(inactive),
                     'state_union':sorted(state_union),'staged':sorted(staged),
                     'planner_only':sorted(planner_only)})
end=time.perf_counter_ns()
summary={'schema':'staged-dependency-acquisition-v1','seed':SEED,'trials':N,
         'elapsed_ms':(end-start)/1e6,'environment':{'python':platform.python_version(),'platform':platform.platform()},
         'modes':{}}
for name,m in metrics.items():
    ds=m.pop('deps')
    summary['modes'][name]={**m,'median_dependencies':statistics.median(ds),
                            'mean_dependencies':statistics.fmean(ds),
                            'p95_dependencies':sorted(ds)[int(.95*(len(ds)-1))]}
assert summary['modes']['staged']['stale_accept']==0
assert summary['modes']['staged']['false_reject']==0
assert summary['modes']['state_union']['stale_accept']==0
assert summary['modes']['state_union']['false_reject']>0
assert summary['modes']['planner_only']['stale_accept']>0
summary['decision']='RETAIN_STAGED_BRANCH_THEN_SELECTED_ACTION_ACQUISITION'
Path(__file__).with_name('summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
Path(__file__).with_name('sample_rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
