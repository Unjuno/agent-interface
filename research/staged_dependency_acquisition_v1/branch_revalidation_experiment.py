import json, random, statistics, platform, time
from pathlib import Path
SEED=202609160228; N=100_000
rng=random.Random(SEED)
methods=['union_phase2','staged_no_branch_revalidate','staged_revalidate']
M={m:{'stale_execute':0,'false_reject':0,'correct_execute':0,'correct_reject':0,'phase2_deps':[]} for m in methods}
examples=[]
start=time.perf_counter_ns()
for i in range(N):
    mode0='A' if rng.getrandbits(1)==0 else 'B'
    selected=mode0
    state={'mode':mode0,'gA':True,'gB':True,'noise':0}
    mutation=rng.choice(['none','inactive_guard','selected_guard','mode_flip','unrelated'])
    if mutation=='inactive_guard': state['gB' if selected=='A' else 'gA']=False
    elif mutation=='selected_guard': state['gA' if selected=='A' else 'gB']=False
    elif mutation=='mode_flip': state['mode']='B' if mode0=='A' else 'A'
    elif mutation=='unrelated': state['noise']=1
    valid=(state['mode']==selected and state['gA' if selected=='A' else 'gB'] is True)
    decisions={
      'union_phase2': state['mode']==selected and state['gA'] and state['gB'],
      'staged_no_branch_revalidate': state['gA' if selected=='A' else 'gB'],
      'staged_revalidate': state['mode']==selected and state['gA' if selected=='A' else 'gB'],
    }
    dep_counts={'union_phase2':3,'staged_no_branch_revalidate':1,'staged_revalidate':2}
    for m,execute in decisions.items():
        if execute and not valid:M[m]['stale_execute']+=1
        elif (not execute) and valid:M[m]['false_reject']+=1
        elif execute:M[m]['correct_execute']+=1
        else:M[m]['correct_reject']+=1
        M[m]['phase2_deps'].append(dep_counts[m])
    if i<100:examples.append({'mode0':mode0,'selected':selected,'mutation':mutation,'state2':state,'valid':valid,'decisions':decisions})
end=time.perf_counter_ns()
summary={'schema':'staged-branch-revalidation-v1','seed':SEED,'trials':N,'elapsed_ms':(end-start)/1e6,'environment':{'python':platform.python_version(),'platform':platform.platform()},'methods':{}}
for m,d in M.items():
    deps=d.pop('phase2_deps');summary['methods'][m]={**d,'median_phase2_dependencies':statistics.median(deps)}
assert summary['methods']['staged_revalidate']['stale_execute']==0 and summary['methods']['staged_revalidate']['false_reject']==0
assert summary['methods']['staged_no_branch_revalidate']['stale_execute']>0
assert summary['methods']['union_phase2']['false_reject']>0
summary['decision']='RETAIN_STAGED_WITH_BRANCH_PREDICATE_REVALIDATION'
Path(__file__).with_name('branch_revalidation_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
Path(__file__).with_name('branch_revalidation_examples.json').write_text(json.dumps(examples,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2,sort_keys=True))
