from __future__ import annotations
import argparse, hashlib, itertools, json, math
from pathlib import Path
from monitor import Monitor,PENDING,SATISFIED,VIOLATED,EXPIRED,UNKNOWN

TASK='TEMPORAL-CONTRACT-MONITOR-COMPILATION-R0-20260918-001'
TIMES=tuple(range(5))
PARAMS=(1,2,3)
LABELS={
 'AB':(frozenset(),frozenset({'A'}),frozenset({'B'}),frozenset({'A','B'})),
 'CD':(frozenset(),frozenset({'C'}),frozenset({'D'}),frozenset({'C','D'})),
 'XY':(frozenset(),frozenset({'X'}),frozenset({'Y'}),frozenset({'X','Y'})),
}

def grouped_labels(history):
    groups=[]
    for t,lab in history:
        if groups and t<groups[-1][0]: return None
        if groups and t==groups[-1][0]: groups[-1][1].update(lab)
        else: groups.append([t,set(lab)])
    return groups

def oracle(kind,param,history):
    if kind=='P':
        last=-10**9
        groups=[]
        for t,val in history:
            if t<last: return UNKNOWN
            last=t
            if groups and t==groups[-1][0]: groups[-1][1]=val
            else: groups.append([t,val])
        p=False;start=None
        for i,(t,val) in enumerate(groups):
            if i>0:
                if p and start is not None and t-start>=param: return SATISFIED
            if val:
                if not p: start=t
                p=True
            else:
                p=False;start=None
        return PENDING

    groups=grouped_labels(history)
    if groups is None: return UNKNOWN
    if not groups: return PENDING
    last_t=groups[-1][0]

    if kind=='AB':
        anchor=next((t for t,l in groups if 'A' in l),None)
        if anchor is None: return PENDING
        if any('B' in l and anchor<=t<=anchor+param for t,l in groups): return SATISFIED
        if last_t>anchor+param: return EXPIRED
        return PENDING

    if kind=='CD':
        d=next((t for t,l in groups if 'D' in l),None)
        c=next((t for t,l in groups if 'C' in l),None)
        if d is not None:
            return VIOLATED if c is not None and c<d else SATISFIED
        if c is not None and c<last_t: return VIOLATED
        return PENDING

    if kind=='XY':
        anchor=next((t for t,l in groups if 'X' in l),None)
        if anchor is None: return PENDING
        if any('Y' in l and anchor<t<=anchor+param for t,l in groups): return VIOLATED
        if last_t>anchor+param: return SATISFIED
        return PENDING
    raise ValueError(kind)

def traces_event(kind,n):
    for ts in itertools.combinations_with_replacement(TIMES,n):
        for labs in itertools.product(LABELS[kind],repeat=n):
            yield tuple(zip(ts,labs))

def traces_p(n):
    for ts in itertools.combinations_with_replacement(TIMES,n):
        for vals in itertools.product((False,True),repeat=n):
            yield tuple(zip(ts,vals))

def compare_family(kind,param):
    traces=prefixes=mismatches=0
    outcomes=set()
    final_counts={x:0 for x in (PENDING,SATISFIED,VIOLATED,EXPIRED,UNKNOWN)}
    examples=[]
    for n in range(6):
        source=traces_p(n) if kind=='P' else traces_event(kind,n)
        for tr in source:
            traces+=1
            m=Monitor(kind,param)
            if n==0:
                prefixes+=1
                got=m.status;exp=oracle(kind,param,())
                outcomes.add(got);final_counts[got]+=1
                if got!=exp: mismatches+=1
                continue
            hist=[]
            bad=False
            for step in tr:
                hist.append(step)
                got=m.feed(*step); exp=oracle(kind,param,hist)
                prefixes+=1; outcomes.add(got)
                if got!=exp:
                    mismatches+=1;bad=True
                    if len(examples)<8: examples.append({'trace':repr(tr),'prefix_len':len(hist),'got':got,'expected':exp})
                    break
            if not bad: final_counts[m.status]+=1
    return {'traces':traces,'prefix_checks':prefixes,'mismatches':mismatches,'outcomes_seen':sorted(outcomes),'final_counts':final_counts,'examples':examples}

def mutant_controls():
    controls={}
    # Closed deadline: equality must satisfy.
    tr=[(0,{'A'}),(2,{'B'})]; correct=oracle('AB',2,tr)
    mutant=EXPIRED if max(t for t,_ in tr)>=2 else PENDING
    controls['deadline_equality']=correct==SATISFIED and mutant!=correct
    # Repeated A must not restart.
    tr=[(0,{'A'}),(1,{'A'}),(3,{'B'})]; correct=oracle('AB',2,tr)
    mutant=SATISFIED
    controls['repeated_A_no_restart']=correct==EXPIRED and mutant!=correct
    # False resets P continuity.
    tr=[(0,True),(1,False),(1,True),(2,True)]; correct=oracle('P',2,tr)
    mutant=SATISFIED
    controls['P_false_resets']=correct==PENDING and mutant!=correct
    # Same-time C,D: C is not strictly before D.
    tr=[(0,{'C'}),(0,{'D'})]; correct=oracle('CD',None,tr); mutant=VIOLATED
    controls['CD_same_time']=correct==SATISFIED and mutant!=correct
    # Same-time X,Y: Y is not strictly after X.
    tr=[(0,{'Y'}),(0,{'X'}),(2,set())]; correct=oracle('XY',1,tr); mutant=VIOLATED
    controls['XY_same_time']=correct==SATISFIED and mutant!=correct
    # Descending time must fail closed.
    m=Monitor('AB',1);m.feed(2,{'A'});correct=m.feed(1,set());mutant=PENDING
    controls['descending_time_unknown']=correct==UNKNOWN and mutant!=correct
    return controls

def malformed_controls():
    rows={}
    for kind,param,val1,val2 in [
      ('AB',1,{'A'},set()),('P',1,False,False),('CD',None,set(),set()),('XY',1,{'X'},set())
    ]:
        m=Monitor(kind,param);m.feed(2,val1);rows[kind]=m.feed(1,val2)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    families={}
    total_traces=total_prefix=mismatches=0
    for kind in ('AB','P','CD','XY'):
        params=(None,) if kind=='CD' else PARAMS
        for p in params:
            key=f'{kind}:{p}'
            r=compare_family(kind,p);families[key]=r
            total_traces+=r['traces'];total_prefix+=r['prefix_checks'];mismatches+=r['mismatches']
    expected_outcomes={
      'AB':{PENDING,SATISFIED,EXPIRED},
      'P':{PENDING,SATISFIED},
      'CD':{PENDING,SATISFIED,VIOLATED},
      'XY':{PENDING,SATISFIED,VIOLATED},
    }
    outcome_checks={}
    for kind in ('AB','P','CD','XY'):
        seen=set()
        for k,v in families.items():
            if k.startswith(kind+':'): seen.update(v['outcomes_seen'])
        outcome_checks[kind]=seen==expected_outcomes[kind]
    malformed=malformed_controls(); corrupt=mutant_controls()
    state_shape=Monitor('AB',1).state_shape()
    checks={
      'mismatch0':mismatches==0,
      'reachable_outcomes':all(outcome_checks.values()),
      'malformed_unknown':all(v==UNKNOWN for v in malformed.values()),
      'constant_state_shape':len(state_shape)==8,
      'corruptions':all(corrupt.values()),
    }
    decision='PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_SCOPED' if all(checks.values()) else 'FAIL_TEMPORAL_MONITOR_SEMANTICS'
    result={
      'task':TASK,'decision':decision,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'times':list(TIMES),'params':list(PARAMS),'max_trace_length':5,
      'families':families,'total_traces':total_traces,'total_prefix_checks':total_prefix,'total_mismatches':mismatches,
      'expected_outcomes':{k:sorted(v) for k,v in expected_outcomes.items()},'outcome_checks':outcome_checks,
      'malformed_controls':malformed,'corruption_controls':corrupt,'state_shape':list(state_shape),'checks':checks,
    }
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode();result['digest']=hashlib.sha256(raw).hexdigest()
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'total_traces':total_traces,'total_prefix_checks':total_prefix,'mismatches':mismatches,'digest':result['digest']},sort_keys=True))
    raise SystemExit(0 if decision.startswith('PASS_') else 1)
if __name__=='__main__':main()
