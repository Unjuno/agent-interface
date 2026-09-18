from __future__ import annotations
import argparse,itertools,json,hashlib
from pathlib import Path
from monitor import Monitor,PENDING,SATISFIED,VIOLATED,EXPIRED,UNKNOWN

TIMES=tuple(range(5));PARAMS=(1,2,3)
OPTS={
 'AB':(set(),{'A'},{'B'},{'A','B'}),
 'CD':(set(),{'C'},{'D'},{'C','D'}),
 'XY':(set(),{'X'},{'Y'},{'X','Y'}),
}

def oracle2(kind,param,h):
    if any(h[i][0]<h[i-1][0] for i in range(1,len(h))): return UNKNOWN
    if kind=='P':
        grouped=[]
        for t,v in h:
            if grouped and grouped[-1][0]==t: grouped[-1]=(t,v)
            else: grouped.append((t,v))
        active=False;start=None
        for i,(t,v) in enumerate(grouped):
            if i and active and t-start>=param: return SATISFIED
            if v:
                if not active:start=t
                active=True
            else:active=False;start=None
        return PENDING
    grouped=[]
    for t,l in h:
        if grouped and grouped[-1][0]==t: grouped[-1][1].update(l)
        else: grouped.append([t,set(l)])
    if not grouped:return PENDING
    last=grouped[-1][0]
    if kind=='AB':
        a=next((t for t,l in grouped if 'A'in l),None)
        if a is None:return PENDING
        if any('B'in l and a<=t<=a+param for t,l in grouped):return SATISFIED
        return EXPIRED if last>a+param else PENDING
    if kind=='CD':
        c=next((t for t,l in grouped if 'C'in l),None);d=next((t for t,l in grouped if 'D'in l),None)
        if d is not None:return VIOLATED if c is not None and c<d else SATISFIED
        return VIOLATED if c is not None and c<last else PENDING
    if kind=='XY':
        x=next((t for t,l in grouped if 'X'in l),None)
        if x is None:return PENDING
        if any('Y'in l and x<t<=x+param for t,l in grouped):return VIOLATED
        return SATISFIED if last>x+param else PENDING
    raise ValueError

def run():
    total=prefixes=mm=0;family_counts={}
    for kind in ('AB','P','CD','XY'):
        params=(None,) if kind=='CD' else PARAMS
        for param in params:
            tc=pc=0
            for n in range(6):
                for ts in itertools.combinations_with_replacement(TIMES,n):
                    vals=(itertools.product((False,True),repeat=n) if kind=='P' else itertools.product(OPTS[kind],repeat=n))
                    for vv in vals:
                        tc+=1;total+=1;m=Monitor(kind,param)
                        if n==0:
                            pc+=1;prefixes+=1
                            if m.status!=oracle2(kind,param,[]):mm+=1
                            continue
                        hist=[]
                        for step in zip(ts,vv):
                            hist.append(step);got=m.feed(*step);exp=oracle2(kind,param,hist)
                            pc+=1;prefixes+=1
                            if got!=exp:mm+=1;break
            family_counts[f'{kind}:{param}']={'traces':tc,'prefix_checks':pc}
    return total,prefixes,mm,family_counts

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
    total,prefixes,mm,fc=run()
    checks={
      'decision':r['decision']=='PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_SCOPED',
      'formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
      'mismatch0':mm==r['total_mismatches']==0,
      'total_traces':total==r['total_traces'],
      'prefix_checks':prefixes==r['total_prefix_checks'],
      'family_counts':all(r['families'][k]['traces']==v['traces'] and r['families'][k]['prefix_checks']==v['prefix_checks'] for k,v in fc.items()),
      'malformed':all(v==UNKNOWN for v in r['malformed_controls'].values()),
      'corruptions':all(r['corruption_controls'].values()),
      'outcomes':all(r['outcome_checks'].values()),
      'state_shape':len(r['state_shape'])==8,
    }
    z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'recomputed_total_traces':total,'recomputed_prefix_checks':prefixes,'recomputed_mismatches':mm,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
    o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
