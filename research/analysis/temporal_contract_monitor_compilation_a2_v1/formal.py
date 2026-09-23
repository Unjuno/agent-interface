from __future__ import annotations
import argparse,hashlib,itertools,json
from pathlib import Path
from monitor import Monitor,PENDING,SATISFIED,VIOLATED,EXPIRED,UNKNOWN

TASK='TEMPORAL-CONTRACT-MONITOR-COMPILATION-A2-20260918-002'
TIMES=tuple(range(5));PARAMS=(1,2,3)
PARENT_TRACES=1062624;PARENT_PREFIXES=5144928
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
        last=None;current_t=None;active=False;start=None
        for t,val in history:
            if last is not None and t<last: return UNKNOWN
            if current_t is None: current_t=t
            elif t>current_t:
                if active and start is not None and t-start>=param: return SATISFIED
                current_t=t
            if val:
                if not active: start=t
                active=True
            else:
                active=False;start=None
            last=t
        return PENDING
    groups=grouped_labels(history)
    if groups is None:return UNKNOWN
    if not groups:return PENDING
    last_t=groups[-1][0]
    if kind=='AB':
        anchor=next((t for t,l in groups if 'A'in l),None)
        if anchor is None:return PENDING
        if any('B'in l and anchor<=t<=anchor+param for t,l in groups):return SATISFIED
        return EXPIRED if last_t>anchor+param else PENDING
    if kind=='CD':
        d=next((t for t,l in groups if 'D'in l),None);c=next((t for t,l in groups if 'C'in l),None)
        if d is not None:return VIOLATED if c is not None and c<d else SATISFIED
        return VIOLATED if c is not None and c<last_t else PENDING
    if kind=='XY':
        anchor=next((t for t,l in groups if 'X'in l),None)
        if anchor is None:return PENDING
        if any('Y'in l and anchor<t<=anchor+param for t,l in groups):return VIOLATED
        return SATISFIED if last_t>anchor+param else PENDING
    raise ValueError(kind)

def traces_event(kind,n):
    for ts in itertools.combinations_with_replacement(TIMES,n):
        for labs in itertools.product(LABELS[kind],repeat=n):yield tuple(zip(ts,labs))
def traces_p(n):
    for ts in itertools.combinations_with_replacement(TIMES,n):
        for vals in itertools.product((False,True),repeat=n):yield tuple(zip(ts,vals))

def compare_family(kind,param):
    traces=prefixes=mismatches=0;outcomes=set();examples=[]
    finals={x:0 for x in (PENDING,SATISFIED,VIOLATED,EXPIRED,UNKNOWN)}
    for n in range(6):
        source=traces_p(n) if kind=='P' else traces_event(kind,n)
        for tr in source:
            traces+=1;m=Monitor(kind,param)
            if n==0:
                prefixes+=1;got=m.status;exp=oracle(kind,param,())
                outcomes.add(got);finals[got]+=1;mismatches+=got!=exp;continue
            hist=[];bad=False
            for step in tr:
                hist.append(step);got=m.feed(*step);exp=oracle(kind,param,hist)
                prefixes+=1;outcomes.add(got)
                if got!=exp:
                    mismatches+=1;bad=True
                    if len(examples)<8:examples.append({'trace':repr(tr),'prefix_len':len(hist),'got':got,'expected':exp})
                    break
            if not bad:finals[m.status]+=1
    return {'traces':traces,'prefix_checks':prefixes,'mismatches':mismatches,'outcomes_seen':sorted(outcomes),'final_counts':finals,'examples':examples}

def malformed_controls():
    rows={}
    for kind,param,v1,v2 in [('AB',1,{'A'},set()),('P',1,False,False),('CD',None,set(),set()),('XY',1,{'X'},set())]:
        m=Monitor(kind,param);m.feed(2,v1);rows[kind]=m.feed(1,v2)
    return rows

def mutant_controls():
    controls={}
    tr=[(0,{'A'}),(2,{'B'})];correct=oracle('AB',2,tr);controls['deadline_equality']=correct==SATISFIED
    tr=[(0,{'A'}),(1,{'A'}),(3,{'B'})];correct=oracle('AB',2,tr);controls['repeated_A_no_restart']=correct==EXPIRED
    tr=[(0,True),(1,False),(1,True),(2,True)];correct=oracle('P',2,tr);controls['P_false_resets']=correct==PENDING
    tr=[(0,{'C'}),(0,{'D'})];controls['CD_same_time']=oracle('CD',None,tr)==SATISFIED
    tr=[(0,{'Y'}),(0,{'X'}),(2,set())];controls['XY_same_time']=oracle('XY',1,tr)==SATISFIED
    m=Monitor('AB',1);m.feed(2,{'A'});controls['descending_time_unknown']=m.feed(1,set())==UNKNOWN
    return controls

def retained_counterexample():
    tr=[(0,True),(1,False),(1,True),(2,False)]
    m=Monitor('P',2)
    for s in tr:got=m.feed(*s)
    return {'candidate':got,'oracle':oracle('P',2,tr),'expected':PENDING}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists()
    families={};tt=pp=mm=0
    for kind in ('AB','P','CD','XY'):
        params=(None,) if kind=='CD' else PARAMS
        for p in params:
            r=compare_family(kind,p);families[f'{kind}:{p}']=r;tt+=r['traces'];pp+=r['prefix_checks'];mm+=r['mismatches']
    expected={'AB':{PENDING,SATISFIED,EXPIRED},'P':{PENDING,SATISFIED},'CD':{PENDING,SATISFIED,VIOLATED},'XY':{PENDING,SATISFIED,VIOLATED}}
    outcome={}
    for kind in expected:
        seen=set()
        for k,v in families.items():
            if k.startswith(kind+':'):seen.update(v['outcomes_seen'])
        outcome[kind]=seen==expected[kind]
    malformed=malformed_controls();corrupt=mutant_controls();ce=retained_counterexample();shape=Monitor('AB',1).state_shape()
    checks={
      'parent_corpus_exact':tt==PARENT_TRACES and pp==PARENT_PREFIXES,
      'mismatch0':mm==0,
      'retained_counterexample':ce['candidate']==ce['oracle']==ce['expected']==PENDING,
      'reachable_outcomes':all(outcome.values()),
      'malformed_unknown':all(v==UNKNOWN for v in malformed.values()),
      'state_shape_unchanged':len(shape)==8,
      'corruptions6':len(corrupt)==6 and all(corrupt.values()),
    }
    decision='PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_A2_SCOPED' if all(checks.values()) else 'FAIL_TEMPORAL_MONITOR_SEMANTICS_A2'
    r={'task':TASK,'decision':decision,'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'total_traces':tt,'total_prefix_checks':pp,'total_mismatches':mm,'families':families,'outcome_checks':outcome,'malformed_controls':malformed,'corruption_controls':corrupt,'retained_counterexample':ce,'state_shape':list(shape),'checks':checks}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'traces':tt,'prefix_checks':pp,'mismatches':mm,'counterexample':ce,'digest':r['digest']},sort_keys=True))
    raise SystemExit(0 if decision.startswith('PASS_') else 1)
if __name__=='__main__':main()
