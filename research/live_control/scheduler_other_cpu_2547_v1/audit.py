#!/usr/bin/env python3
"""Raw-only independent reconstruction. Never imports run.py or executes a load."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

ARMS=('IDLE','SAME_CORE','OTHER_CORE')


def quantile(xs,q):
    ys=sorted(xs); k=(len(ys)-1)*q; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo]*(hi-k)+ys[hi]*(k-lo) if hi!=lo else ys[lo]


def describe(xs):
    return dict(n=len(xs),p50_ns=quantile(xs,.5),p95_ns=quantile(xs,.95),
                p99_ns=quantile(xs,.99),max_ns=max(xs))


def reconstruct(rows):
    errors=[]
    def check(ok,reason):
        if not ok: errors.append(reason)
    def integer(x): return type(x) is int
    def identity(obj,cpu):
        return (type(obj) is dict and all(integer(obj.get(k)) for k in
                ('pid','tid','cpu','scheduler','nice')) and obj['pid']>0 and obj['tid']>0
                and type(obj.get('affinity')) is list and len(obj['affinity'])==1
                and integer(obj['affinity'][0]) and obj['affinity']==[cpu]
                and obj['cpu']==cpu and obj['scheduler']==0 and obj['nice']==0)
    check(len(rows)==90,'block_count')
    if len(rows)!=90: return dict(errors=errors,decision='FAIL_MEASUREMENT_BINDING')
    maxima={a:[] for a in ARMS}; pooled={a:[] for a in ARMS}; block_stats=[]
    orders=list(itertools.permutations(ARMS))*5
    last_wall=0
    for index,r in enumerate(rows):
        label=f'block{index}:'
        try:
            triplet,position=divmod(index,3); arm=orders[triplet][position]
            check(integer(r['triplet']) and r['triplet']==triplet,label+'triplet')
            check(integer(r['position']) and r['position']==position,label+'position')
            check(r['arm']==arm,label+'arm')
            check(identity(r['before'],0) and identity(r['after'],0),label+'observer_identity')
            check(r['before']['pid']==r['after']['pid'] and r['before']['tid']==r['after']['tid'],label+'observer_binding')
            for key in ('wall','process','thread'):
                value=r[key]
                check(type(value) is list and len(value)==2 and all(integer(x) for x in value)
                      and value[1]>value[0]>=0,label+key)
            check(r['wall'][0]>last_wall,label+'block_order'); last_wall=r['wall'][1]
            child=r['child']
            if arm=='IDLE':
                check(child is None and r['child_alive_before'] is False
                      and r['child_alive_after'] is False,label+'idle_child')
            else:
                cpu=0 if arm=='SAME_CORE' else 1
                ready=child['ready']; end=child['terminal']
                check(identity(ready['identity'],cpu) and identity(end['identity'],cpu),label+'child_identity')
                check(integer(child['pid']) and child['pid']==ready['identity']['pid']==end['identity']['pid'],label+'child_pid')
                check(child['pid']!=r['before']['pid'],label+'separate_process')
                check(child['observed_affinity']==[cpu] and all(integer(v) for v in child['observed_affinity']),label+'observed_affinity')
                check(ready['kind']=='ready' and end['kind']=='stopped',label+'child_protocol')
                check(all(integer(e[k]) for e in (ready,end) for k in ('monotonic_ns','process_ns')),label+'child_clocks')
                check(ready['monotonic_ns']<r['wall'][0]<r['wall'][1]<=end['monotonic_ns'],label+'load_coverage')
                check(end['process_ns']>ready['process_ns']>=0,label+'child_cpu_exposure')
                check(end['timed_out'] is False and child['reaped'] is True and child['stderr']=='',label+'child_cleanup')
                check(integer(child['returncode']) and child['returncode']==0,label+'child_exit')
                check(r['child_alive_before'] is True and r['child_alive_after'] is True,label+'child_liveness')
            samples=r['samples']
            check(type(samples) is list and len(samples)==300,label+'sample_count')
            if len(samples)!=300: continue
            check(all(type(s) is list and len(s)==3 and all(integer(v) for v in s) for s in samples),label+'timestamp_type')
            d0=samples[0][0]
            last_wake=0; values=[]
            for j,(due,wake,late) in enumerate(samples):
                check(due==d0+j*2_000_000,label+f'due_step{j}')
                check(late==wake-due,label+f'primitive_delta{j}')
                check(r['wall'][0]<=wake<=r['wall'][1] and wake>=last_wake,label+f'wake_order{j}')
                last_wake=wake; values.append(max(0,wake-due))
            check(r['wall'][0]<d0<=r['wall'][0]+10_000_000,label+'first_due')
            expected=describe(values)
            expected['late_deadlines_ge_period']=sum(x>=2_000_000 for x in values)
            check(set(r['stats'])==set(expected),label+'stat_keys')
            for k,v in expected.items():
                actual=r['stats'].get(k)
                typed=type(actual) in (int,float) and type(actual) is not bool
                check(typed and math.isclose(actual,v,rel_tol=1e-14,abs_tol=1e-8),label+'stat_'+k)
            check(integer(r['stats']['n']) and integer(r['stats']['late_deadlines_ge_period']),label+'count_types')
            maxima[arm].append(max(values)); pooled[arm].extend(values)
            block_stats.append(dict(index=index,triplet=triplet,arm=arm,**expected))
        except (KeyError,TypeError,ValueError,IndexError,OverflowError) as exc:
            errors.append(label+'schema:'+type(exc).__name__)
    if errors: return dict(errors=errors,decision='FAIL_MEASUREMENT_BINDING')
    ratios=[s/max(i,1) for s,i in zip(maxima['SAME_CORE'],maxima['IDLE'])]
    distances=[abs(o-i)/max(abs(s-i),1) for i,s,o in zip(*(maxima[a] for a in ARMS))]
    metrics=dict(median_same_idle_ratio=statistics.median(ratios),
                 median_same_max_ns=statistics.median(maxima['SAME_CORE']),
                 same_blocks_ge_1ms=sum(x>=1_000_000 for x in maxima['SAME_CORE']),
                 median_other_idle_relative_distance=statistics.median(distances))
    gates=[metrics['median_same_idle_ratio']>=2, metrics['median_same_max_ns']>=1_000_000,
           metrics['same_blocks_ge_1ms']>=15, metrics['median_other_idle_relative_distance']<=.5]
    return dict(errors=errors,decision=('PASS_SAME_CORE_ATTRIBUTION_SCOPED' if all(gates)
                  else 'HOLD_CONTENTION_SOURCE_UNRESOLVED'),metrics=metrics,gates=gates,
                pooled={a:describe(v) for a,v in pooled.items()},
                block_maxima={a:describe(v) for a,v in maxima.items()},
                paired_ratios=ratios,paired_distances=distances,block_stats=block_stats,
                excluded_blocks=0,block_count=90,sample_count=27000)


def audit(root,out):
    root=Path(root); out=Path(out)
    result={}; errors=[]
    try:
        freeze=json.loads((root/'FREEZE.json').read_text())
        for name,digest in freeze['sha256'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
                errors.append('source_hash:'+name)
        expected=[f'block-{i:02d}.json' for i in range(90)]
        if sorted(p.name for p in out.glob('block-*.json'))!=expected:
            errors.append('file_denominator')
        rows=[json.loads((out/name).read_text()) for name in expected]
        result=reconstruct(rows); errors+=result['errors']
        start=json.loads((out/'START.json').read_text()); end=json.loads((out/'END.json').read_text())
        if start['allocation']!='scheduler-other-cpu-20260922-01': errors.append('allocation')
        if start['freeze_sha256']!=hashlib.sha256((root/'FREEZE.json').read_bytes()).hexdigest(): errors.append('freeze_binding')
        if type(end['returncode']) is not int or end['returncode']!=0 or end['completed_blocks']!=90: errors.append('terminal')
        if end['restored_affinity']!=json.loads((root/'environment.json').read_text())['allowed']: errors.append('affinity_restore')
        if not start['monotonic_ns']<rows[0]['wall'][0]<rows[-1]['wall'][1]<end['monotonic_ns']: errors.append('allocation_clock')
        if any(r['before']['pid']!=start['pid'] for r in rows): errors.append('observer_pid')
        if (out/'STOP.json').exists(): errors.append('retained_stop')
        candidate=json.loads((out/'RESULT.json').read_text())
        for k in ('metrics','gates','decision'):
            if candidate.get(k)!=result.get(k): errors.append('candidate_disagreement:'+k)
        result['raw_sha256']={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in expected+['START.json','END.json','RESULT.json']}
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append('incomplete:'+type(exc).__name__+':'+str(exc))
    result['errors']=errors
    result['integrity']='PASS' if not errors else 'FAIL'
    if errors: result['decision']='FAIL_MEASUREMENT_BINDING'
    return result


if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: audit.py SOURCE_ROOT FORMAL_OUTPUT')
    result=audit(sys.argv[1],sys.argv[2])
    print(json.dumps(result,sort_keys=True,indent=2))
    sys.exit(bool(result['errors']))
