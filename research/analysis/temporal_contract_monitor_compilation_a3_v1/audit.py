from __future__ import annotations
import argparse,hashlib,itertools,json
from pathlib import Path
from monitor import Monitor,PENDING,SATISFIED,VIOLATED,EXPIRED,UNKNOWN
TIMES=tuple(range(5));PARAMS=(1,2,3);FULL_TRACES=1062624;FULL_PREFIXES=5144980
OPTS={'AB':(set(),{'A'},{'B'},{'A','B'}),'CD':(set(),{'C'},{'D'},{'C','D'}),'XY':(set(),{'X'},{'Y'},{'X','Y'})}

def ref(kind,param,h):
    if any(h[i][0]<h[i-1][0] for i in range(1,len(h))):return UNKNOWN
    if kind=='P':
        active=False;start=None;prev=None
        for t,v in h:
            if prev is not None and t>prev and active and t-start>=param:return SATISFIED
            if v:
                if not active:start=t
                active=True
            else:active=False;start=None
            prev=t
        return PENDING
    g=[]
    for t,l in h:
        if g and g[-1][0]==t:g[-1][1].update(l)
        else:g.append([t,set(l)])
    if not g:return PENDING
    last=g[-1][0]
    if kind=='AB':
        a=next((t for t,l in g if 'A'in l),None)
        if a is None:return PENDING
        if any('B'in l and a<=t<=a+param for t,l in g):return SATISFIED
        return EXPIRED if last>a+param else PENDING
    if kind=='CD':
        c=next((t for t,l in g if 'C'in l),None);d=next((t for t,l in g if 'D'in l),None)
        if d is not None:return VIOLATED if c is not None and c<d else SATISFIED
        return VIOLATED if c is not None and c<last else PENDING
    x=next((t for t,l in g if 'X'in l),None)
    if x is None:return PENDING
    if any('Y'in l and x<t<=x+param for t,l in g):return VIOLATED
    return SATISFIED if last>x+param else PENDING

def run():
    total=prefixes=mm=0;fc={}
    for kind in ('AB','P','CD','XY'):
        params=(None,) if kind=='CD' else PARAMS
        for p in params:
            tc=pc=0
            for n in range(6):
                for ts in itertools.combinations_with_replacement(TIMES,n):
                    vals=itertools.product((False,True),repeat=n) if kind=='P' else itertools.product(OPTS[kind],repeat=n)
                    for vv in vals:
                        tc+=1;total+=1;m=Monitor(kind,p)
                        if n==0:
                            pc+=1;prefixes+=1;mm+=m.status!=ref(kind,p,[]);continue
                        h=[]
                        for s in zip(ts,vv):
                            h.append(s);pc+=1;prefixes+=1
                            if m.feed(*s)!=ref(kind,p,h):mm+=1;break
            fc[f'{kind}:{p}']={'traces':tc,'prefix_checks':pc}
    return total,prefixes,mm,fc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());o=Path(a.output);assert not o.exists()
    t,p,m,fc=run();ce=[(0,True),(1,False),(1,True),(2,False)];cm=Monitor('P',2)
    for s in ce:cg=cm.feed(*s)
    cr=ref('P',2,ce)
    checks={'decision':r['decision']=='PASS_TEMPORAL_CONTRACT_MONITOR_COMPILATION_A3_SCOPED','formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,'full_counts':t==r['total_traces']==FULL_TRACES and p==r['total_prefix_checks']==FULL_PREFIXES,'mismatch0':m==r['total_mismatches']==0,'family_counts':all(r['families'][k]['traces']==v['traces'] and r['families'][k]['prefix_checks']==v['prefix_checks'] for k,v in fc.items()),'counterexample':cg==cr==PENDING,'corruptions':len(r['corruption_controls'])==6 and all(r['corruption_controls'].values()),'outcomes':all(r['outcome_checks'].values()),'malformed':all(v==UNKNOWN for v in r['malformed_controls'].values()),'shape':len(r['state_shape'])==8}
    z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'recomputed_total_traces':t,'recomputed_prefix_checks':p,'recomputed_mismatches':m,'counterexample_candidate':cg,'counterexample_reference':cr,'result_sha256':hashlib.sha256(Path(a.result).read_bytes()).hexdigest()}
    o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
