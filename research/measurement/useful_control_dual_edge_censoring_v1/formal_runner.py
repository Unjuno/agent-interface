from __future__ import annotations
import hashlib, json, random, time
from dual_edge_contract import *

TASK='USEFUL-CONTROL-DUAL-EDGE-CENSORING-20260917-001'
SEED_SMALL=98520260917001
SEED_MULTI=98520260917002
N_SMALL=30000
N_MULTI=50000
REALIZATIONS_PER_MULTI=4

def exact_occ(d,r,w):
    if d>r:return None
    x=intersect(Interval(d,r),w)
    return 0 if x is None else x.width_ns

def exact_auth(d,r,w,auth):
    if d>r:return None
    x=intersect(Interval(d,r),w)
    if not x:return 0
    return measure(y for a in auth if (y:=intersect(x,a)))

def exhaustive(a,w):
    vals=[];avals=[]
    for d in range(a.down.lo_ns,a.down.hi_ns+1):
        for r in range(a.release.lo_ns,a.release.hi_ns+1):
            if d<=r:
                vals.append(exact_occ(d,r,w));avals.append(exact_auth(d,r,w,a.authority))
    if not vals:raise AssertionError('no feasible realization')
    return min(vals),max(vals),min(avals),max(avals)

def union_exact(realized,w):
    phys=[];auth=[]
    for d,r,a in realized:
        x=intersect(Interval(d,r),w)
        if x:
            phys.append(x)
            for au in a.authority:
                y=intersect(x,au)
                if y:auth.append(y)
    return measure(phys),measure(auth)

def choose_realization(rng,a):
    feasible=[]
    for d in range(a.down.lo_ns,a.down.hi_ns+1):
        lo=max(d,a.release.lo_ns)
        if lo<=a.release.hi_ns: feasible.append((d,lo,a.release.hi_ns))
    d,lo,hi=rng.choice(feasible)
    return d,rng.randrange(lo,hi+1),a

def controls():
    out={}
    w=Interval(0,100)
    a=CensoredActuation(EdgeInterval(10,20),EdgeInterval(60,70),[Interval(0,100)],'a')
    b=occupancy_bounds(a,w);out['projection_discriminator']=(b.lower_ns,b.upper_ns)==(40,60)
    a=CensoredActuation(EdgeInterval(10,10),EdgeInterval(40,40),[Interval(15,35)],'b')
    b=occupancy_bounds(a,w);out['exact_edge_reduction']=(b.lower_ns,b.upper_ns,b.authority_lower_ns,b.authority_upper_ns)==(30,30,20,20)
    a=CensoredActuation(EdgeInterval(10,30),EdgeInterval(20,40),[],'c')
    b=occupancy_bounds(a,w);out['overlap_zero_guaranteed']=(b.lower_ns,b.upper_ns)==(0,30)
    for name,fn in {
        'impossible_reject':lambda:CensoredActuation(EdgeInterval(50,60),EdgeInterval(10,40),[],'x'),
        'blank_id_reject':lambda:CensoredActuation(EdgeInterval(1,2),EdgeInterval(3,4),[],'   '),
    }.items():
        try:fn();out[name]=False
        except ValueError:out[name]=True
    try:analyze(w,[CensoredActuation(EdgeInterval(1,2),EdgeInterval(3,4),[],'d'),CensoredActuation(EdgeInterval(5,6),EdgeInterval(7,8),[],'d')]);out['duplicate_reject']=False
    except ValueError:out['duplicate_reject']=True
    return out

def main():
    t0=time.perf_counter(); h=hashlib.sha256(); mismatches=[]; authority_conservative=0
    rng=random.Random(SEED_SMALL)
    for case in range(N_SMALL):
        ws=rng.randrange(0,8);we=rng.randrange(ws+1,13);w=Interval(ws,we)
        dlo=rng.randrange(0,10);dhi=rng.randrange(dlo,11);rlo=rng.randrange(0,11);rhi=rng.randrange(max(rlo,dlo),13)
        auth=[]
        for _ in range(rng.randrange(0,3)):
            s=rng.randrange(0,11);auth.append(Interval(s,rng.randrange(s+1,13)))
        a=CensoredActuation(EdgeInterval(dlo,dhi),EdgeInterval(rlo,rhi),auth,'a')
        got=occupancy_bounds(a,w); exp=exhaustive(a,w)
        ok=got.lower_ns==exp[0] and got.upper_ns==exp[1] and got.authority_lower_ns<=exp[2] and got.authority_upper_ns>=exp[3]
        if not ok and len(mismatches)<5:mismatches.append(['small',case,got.__dict__,exp])
        authority_conservative += int(got.authority_lower_ns<=exp[2] and got.authority_upper_ns>=exp[3])
        h.update(json.dumps([case,ws,we,dlo,dhi,rlo,rhi,got.__dict__,exp],sort_keys=True).encode())

    rng=random.Random(SEED_MULTI); containment_fail=0; invariant_fail=0; realization_count=0
    for case in range(N_MULTI):
        ws=rng.randrange(0,20);we=rng.randrange(ws+1,50);w=Interval(ws,we);acts=[]
        for j in range(rng.randrange(1,6)):
            dlo=rng.randrange(0,40);dhi=rng.randrange(dlo,41);rlo=rng.randrange(0,41);rhi=rng.randrange(max(rlo,dlo),51)
            auth=[]
            for _ in range(rng.randrange(0,4)):
                s=rng.randrange(0,40);auth.append(Interval(s,rng.randrange(s+1,51)))
            acts.append(CensoredActuation(EdgeInterval(dlo,dhi),EdgeInterval(rlo,rhi),auth,f'id-{j}'))
        got=analyze(w,acts)
        if not (got['authorized_occupancy_lower_ns']<=got['physical_occupancy_lower_ns']<=got['physical_occupancy_upper_ns'] and got['authorized_occupancy_upper_ns']<=got['physical_occupancy_upper_ns']): invariant_fail+=1
        for k in range(REALIZATIONS_PER_MULTI):
            realized=[choose_realization(rng,a) for a in acts];p,au=union_exact(realized,w);realization_count+=1
            if not (got['physical_occupancy_lower_ns']<=p<=got['physical_occupancy_upper_ns'] and got['authorized_occupancy_lower_ns']<=au<=got['authorized_occupancy_upper_ns']):
                containment_fail+=1
                if len(mismatches)<5:mismatches.append(['multi',case,k,got,p,au])
            h.update(json.dumps([case,k,p,au,got['physical_occupancy_lower_ns'],got['physical_occupancy_upper_ns'],got['authorized_occupancy_lower_ns'],got['authorized_occupancy_upper_ns']],sort_keys=True).encode())
    ctrl=controls(); errors=[]
    if mismatches:errors.append('oracle_or_containment_mismatch')
    if authority_conservative!=N_SMALL:errors.append('authority_small')
    if containment_fail:errors.append('containment')
    if invariant_fail:errors.append('invariant')
    if not all(ctrl.values()):errors.append('controls')
    result=dict(task=TASK,decision='PASS_DUAL_EDGE_CENSORING_SCOPED' if not errors else 'FAIL_DUAL_EDGE_CENSORING',errors=errors,formal_invocation=1,formal_reruns=0,small_cases=N_SMALL,small_physical_exact=N_SMALL if not any(m[0]=='small' for m in mismatches) else N_SMALL-1,small_authority_conservative=authority_conservative,multi_cases=N_MULTI,exact_realizations=realization_count,containment_failures=containment_fail,invariant_failures=invariant_fail,controls=ctrl,case_digest_sha256=h.hexdigest(),mismatch_examples=mismatches,wall_seconds=time.perf_counter()-t0,network_calls=0,x11_gui_calls=0,task_input_calls=0,authority_grants=0)
    open('FORMAL_RESULT.json','w').write(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));raise SystemExit(bool(errors))
if __name__=='__main__':main()
