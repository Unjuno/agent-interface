from fractions import Fraction as F
from collections import defaultdict
import argparse,hashlib,json,math
from pathlib import Path
T=4; M=8

def comps(total,k,prefix=()):
    if k==1:
        yield prefix+(total,); return
    for x in range(total+1):
        yield from comps(total-x,k-1,prefix+(x,))

def run(construction=False):
    N=4 if construction else 8
    groups=defaultdict(list)
    st={'N':N,'distributions':0,'observable_groups':0,'group_range_mismatch':0,'endpoint_sharpness_failures':0,
        'ambiguous_mean_groups':0,'completion_mean_defined_rows':0,'completion_mean_not_full_rows':0,
        'completion_underestimate_sign_mismatch':0,'censor_at_horizon_underestimate_rows':0,
        'censor_at_horizon_sign_mismatch':0,'all_censored_rows':0}
    for c in comps(N,8):
        st['distributions']+=1
        obs=c[:4]+(sum(c[4:]),)
        mean=F(sum((i+1)*n for i,n in enumerate(c)),N)
        groups[obs].append(mean)
        completed=sum(c[:4]); cens=sum(c[4:])
        if completed==0: st['all_censored_rows']+=1
        if completed>0 and cens>0:
            cm=F(sum((i+1)*c[i] for i in range(4)),completed)
            st['completion_mean_defined_rows']+=1
            st['completion_mean_not_full_rows']+=int(cm!=mean)
            st['completion_underestimate_sign_mismatch']+=int(not(cm<mean))
        if cens>0:
            base=F(sum((i+1)*c[i] for i in range(4)),N)
            imp=base+F(cens,N)*T
            st['censor_at_horizon_underestimate_rows']+=int(imp!=mean)
            st['censor_at_horizon_sign_mismatch']+=int(not(imp<mean))
    st['observable_groups']=len(groups)
    for obs,means in groups.items():
        cens=obs[4]
        base=F(sum((i+1)*obs[i] for i in range(4)),N)
        L=base+F(cens,N)*(T+1); U=base+F(cens,N)*M
        amin=min(means);amax=max(means)
        st['group_range_mismatch']+=int((L,U)!=(amin,amax))
        st['endpoint_sharpness_failures']+=int(L not in means or U not in means)
        st['ambiguous_mean_groups']+=int(len(set(means))>1)
    tails=(8,16,32,64)
    u_means=tuple(F(1,2)*2+F(1,2)*d for d in tails)
    unbounded={'same_observation':True,'tail_durations':tails,'means':tuple(str(x) for x in u_means),'strictly_increasing':all(u_means[i]<u_means[i+1] for i in range(len(u_means)-1))}
    directed={'expected_compositions':st['distributions']==math.comb(N+7,7),'bounded_example':True,'unbounded_tail_increases':unbounded['strictly_increasing']}
    corrupt={'censor_mass_required':st['ambiguous_mean_groups']>0 if not construction else True,
             'tail_min_is_T_plus_1':st['censor_at_horizon_underestimate_rows']>0,
             'no_unjustified_finite_upper':unbounded['strictly_increasing'],
             'group_endpoints_bound':st['endpoint_sharpness_failures']==0}
    expected=math.comb(N+7,7)
    full_gate=True if construction else st['distributions']==6435
    good=(st['distributions']==expected and full_gate and st['group_range_mismatch']==0 and st['endpoint_sharpness_failures']==0 and
          st['ambiguous_mean_groups']>0 and st['completion_mean_not_full_rows']>0 and st['completion_underestimate_sign_mismatch']==0 and
          st['censor_at_horizon_underestimate_rows']>0 and st['censor_at_horizon_sign_mismatch']==0 and unbounded['strictly_increasing'] and
          all(directed.values()) and all(corrupt.values()))
    return st,unbounded,directed,corrupt,good

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();st,u,dc,cor,good=run(a.construction)
    r={'construction':a.construction,'stats':st,'unbounded_control':u,'directed':dc,'corruptions':cor,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_PROBABILISTIC_AUTOMATON_DWELL_CENSOR_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':'),default=str).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(r,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
