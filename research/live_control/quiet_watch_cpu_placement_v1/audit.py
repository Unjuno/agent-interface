#!/usr/bin/env python3
"""Independent arithmetic/schedule/integrity auditor; imports no measurement code."""
import hashlib, json, statistics, sys
from pathlib import Path

def require(ok, label):
    if not ok: raise ValueError(label)

def integer(x): return type(x) is int

def quantile(xs, p):
    v = sorted(xs); q = (len(v)-1)*p; lo = int(q); hi = min(lo+1,len(v)-1)
    return v[lo]*(1-(q-lo))+v[hi]*(q-lo)

def inspect(raw, plan, freeze, preflight=False):
    require(raw['schema']=='cpu_placement_v1' and raw['task']==plan['task'], 'identity')
    require(raw['mode']==('preflight' if preflight else 'measure'), 'mode')
    require('error' not in raw and raw['source_sha256']==freeze['sha256'], 'source/error')
    e = raw['environment']; cpu=e['observer_cpu']; other=e['other_cpu']
    require(cpu==min(e['initial_affinity']) and other in e['initial_affinity'] and other!=cpu,'cpu selection')
    a=e['topology'][str(cpu)]; b=e['topology'][str(other)]
    require(a['core_id'] is not None and b['core_id'] is not None and a['core_id']!=b['core_id']
            and a['physical_package_id']==b['physical_package_id'], 'guest topology')
    require(e['policy']==0 and e['nice']==0, 'priority')
    orders=plan['orders'][:1] if preflight else plan['orders']
    require(len(raw['blocks'])==3*len(orders), 'block count')
    stats=[]; previous_end=0
    for i,r in enumerate(raw['blocks']):
        require(r['index']==i and r['triplet']==i//3 and r['arm']==orders[i//3][i%3], 'schedule')
        require(r['parent_affinity_before']==[cpu] and r['parent_affinity_after']==[cpu], 'parent affinity')
        start=r['start_ns']; end=r['end_ns']
        require(integer(start) and integer(end) and previous_end<start<end, 'block brackets')
        previous_end=end
        require(all(integer(r[k]) and 0<=r[k]<=end-start for k in ('thread_cpu_ns','process_cpu_ns')), 'cpu timing')
        samples=r['samples']; require(len(samples)==plan['samples_per_block'], 'sample count')
        prev=start; late=[]; gaps=[]
        for j,row in enumerate(samples):
            require(type(row) is list and len(row)==3 and all(integer(x) for x in row), 'tuple type')
            due,wake,lateness=row
            require(due==start+plan['start_delay_ns']+j*plan['period_ns'], 'due arithmetic')
            require(lateness==wake-due and lateness>=0, 'lateness arithmetic')
            require(prev<=wake<=end, 'wake ordering/bracket')
            if j: gaps.append(wake-prev)
            prev=wake; late.append(lateness)
        child=r['child']
        if r['arm']=='idle': require(child is None,'idle child')
        else:
            dest=cpu if r['arm']=='same' else other
            require(child['requested_cpu']==dest, 'child destination')
            require(child['ready']['affinity']==[dest] and child['affinity_before']==[dest]
                    and child['affinity_after']==[dest], 'child affinity')
            require(child['ready']['policy']==0 and child['ready']['nice']==0, 'child priority')
            require(child['alive_before'] is True and child['alive_after'] is True, 'child liveness')
            require(integer(child['ticks_before']) and integer(child['ticks_after'])
                    and child['ticks_after']>child['ticks_before'], 'child CPU progress')
            require(child['exit_code']==-15, 'child cleanup')
        stats.append({'index':i,'triplet':i//3,'arm':r['arm'],'max_late_ns':max(late),
            'p99_late_ns':quantile(late,.99),'p50_late_ns':quantile(late,.50),
            'overdue_deadlines':sum(x>=plan['period_ns'] for x in late),'max_wake_gap_ns':max(gaps)})
    ratios=[]; same=[]; paired=[]
    for i in range(len(orders)):
        arms={s['arm']:s for s in stats[i*3:i*3+3]}
        sm=arms['same']['max_late_ns']; ot=arms['other']['max_late_ns']; idle=arms['idle']['max_late_ns']
        ratio=ot/max(sm,1); ratios.append(ratio); same.append(sm)
        paired.append({'triplet':i,'same_max_ns':sm,'other_max_ns':ot,'idle_max_ns':idle,
                       'other_same_ratio':ratio,'same_idle_ratio':sm/max(idle,1)})
    med=statistics.median(ratios); n=sum(x<=plan['ratio_max'] for x in ratios); smed=statistics.median(same)
    decision='CPU_PLACEMENT_EFFECT_SCOPED' if med<=plan['ratio_max'] and n>=plan['required_pairs'] and smed>=plan['same_max_floor_ns'] else 'HOLD_CPU_PLACEMENT'
    return {'integrity_pass':True,'decision':'PREFLIGHT_ONLY' if preflight else decision,
            'median_other_same_ratio':med,'pairs_at_or_below_ratio':n,'same_median_max_ns':smed,
            'arms':{arm:{'median_max_ns':statistics.median(s['max_late_ns'] for s in stats if s['arm']==arm),
                         'median_p99_ns':statistics.median(s['p99_late_ns'] for s in stats if s['arm']==arm)}
                    for arm in ('idle','same','other')},'pairs':paired,'blocks':stats}

def main():
    root=Path(__file__).resolve().parent
    plan=json.loads((root/'plan.json').read_text()); freeze=json.loads((root/'freeze.json').read_text())
    for name,digest in freeze['sha256'].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'file hash: '+name)
    raw=json.loads(Path(sys.argv[1]).read_text())
    result=inspect(raw,plan,freeze,'--preflight' in sys.argv)
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__': main()
