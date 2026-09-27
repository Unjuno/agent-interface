from __future__ import annotations
import argparse, hashlib, json, math, random
from collections import Counter
from pathlib import Path

TASK='SAFE-PROBE-MINIMAX-VERSION-SPACE-R0-20260919-001'
SEED=183620260919001

def counts(outputs):
    return sorted(Counter(outputs).values(), reverse=True)
def worst(outputs):
    c=counts(outputs)
    return max(c) if c else 0
def entropy_product(outputs):
    if not outputs: return None
    z=1
    for c in Counter(outputs).values(): z *= c**c
    return z
def candidate(probes):
    safe=[(i,p) for i,p in enumerate(probes) if p['safe']]
    if not safe: return None
    return min(safe, key=lambda ip:(worst(ip[1]['outputs']), ip[0]))[0]
def oracle(probes):
    safe=[(i,p) for i,p in enumerate(probes) if p['safe']]
    if not safe: return None
    best=None
    for i,p in safe:
        w=0
        for o in set(p['outputs']):
            survivors=sum(x==o for x in p['outputs'])
            w=max(w,survivors)
        key=(w,i)
        if best is None or key<best[0]: best=(key,i)
    return best[1]
def entropy_pick(probes):
    safe=[(i,p) for i,p in enumerate(probes) if p['safe']]
    if not safe:return None
    return min(safe,key=lambda ip:(entropy_product(ip[1]['outputs']),ip[0]))[0]
def partitions(n,max_parts=6,min_part=1):
    def rec(rem,largest,parts):
        if rem==0:
            yield tuple(parts); return
        if len(parts)>=max_parts:return
        for x in range(min(largest,rem),0,-1):
            yield from rec(rem-x,x,parts+[x])
    yield from rec(n,n,[])
def outputs_from_profile(profile, offset=0):
    out=[]
    for label,c in enumerate(profile): out += [label+offset]*c
    return out
def directed():
    a={'safe':True,'outputs':outputs_from_profile((4,1,1,1,1))}
    b={'safe':True,'outputs':outputs_from_profile((3,3,2))}
    unsafe={'safe':False,'outputs':list(range(8))}
    noinfo={'safe':True,'outputs':[0]*8}
    pair=[a,b]
    return {'minimax_example':candidate(pair),'entropy_example':entropy_pick(pair),'minimax_worst':worst(pair[candidate(pair)]['outputs']),'entropy_worst':worst(pair[entropy_pick(pair)]['outputs']),'unsafe_perfect_ignored':candidate([unsafe,b]),'empty_safe':candidate([unsafe]),'noinfo_worst':worst(noinfo['outputs'])}
def exhaustive(max_n):
    rows=0;mismatch=0;pair_order_mismatch=0
    for n in range(2,max_n+1):
        ps=list(partitions(n,6))
        for pa in ps:
            for pb in ps:
                probes=[{'safe':True,'outputs':outputs_from_profile(pa)},{'safe':True,'outputs':outputs_from_profile(pb,100)}]
                c=candidate(probes);o=oracle(probes);rows+=1
                if c!=o:mismatch+=1
                expected=0 if (max(pa),0) <= (max(pb),1) else 1
                if c!=expected:pair_order_mismatch+=1
    return rows,mismatch,pair_order_mismatch
def random_formal(nrows):
    rng=random.Random(SEED); mismatch=unsafe_sel=label_change=entropy_worse=0; empty_safe_checks=0; stream=hashlib.sha256(); examples=[]
    for case in range(nrows):
        nh=rng.randint(2,16); np=rng.randint(2,8); probes=[]; no_safe=(case%50==0)
        for j in range(np):
            outk=rng.randint(1,min(6,nh)); outs=[rng.randrange(outk) for _ in range(nh)]; safe=False if no_safe else (rng.random()<0.65); probes.append({'safe':safe,'outputs':outs})
        if not no_safe and not any(p['safe'] for p in probes): probes[0]['safe']=True
        c=candidate(probes);o=oracle(probes)
        if c!=o:mismatch+=1
        if c is not None and not probes[c]['safe']:unsafe_sel+=1
        if no_safe:
            empty_safe_checks+=1
            if c is not None:mismatch+=1
        perm=[]
        for p in probes:
            labels=sorted(set(p['outputs'])); shuffled=labels[:];rng.shuffle(shuffled); mp=dict(zip(labels,shuffled))
            perm.append({'safe':p['safe'],'outputs':[mp[x] for x in p['outputs']]})
        if candidate(perm)!=c:label_change+=1
        e=entropy_pick(probes)
        if c is not None and e is not None and worst(probes[e]['outputs'])>worst(probes[c]['outputs']):
            entropy_worse+=1
            if len(examples)<5: examples.append({'case':case,'minimax':c,'entropy':e,'minimax_counts':counts(probes[c]['outputs']),'entropy_counts':counts(probes[e]['outputs'])})
        rec={'case':case,'nh':nh,'safe':[p['safe'] for p in probes],'profiles':[counts(p['outputs']) for p in probes],'candidate':c,'oracle':o,'entropy':e}
        stream.update((json.dumps(rec,sort_keys=True,separators=(',',':'))+'\n').encode())
    return {'rows':nrows,'candidate_oracle_mismatch':mismatch,'unsafe_selected':unsafe_sel,'label_permutation_changes':label_change,'entropy_worse_worstcase':entropy_worse,'empty_safe_cases':empty_safe_checks,'examples':examples,'stream_sha256':stream.hexdigest()}
def execute(random_rows, exhaustive_n):
    exrows,exmis,exord=exhaustive(exhaustive_n); rnd=random_formal(random_rows); d=directed(); formal=(random_rows==250000 and exhaustive_n==16)
    gates=[exmis==0,exord==0,rnd['candidate_oracle_mismatch']==0,rnd['unsafe_selected']==0,rnd['label_permutation_changes']==0,rnd['entropy_worse_worstcase']>0,d['minimax_example']==1,d['entropy_example']==0,d['minimax_worst']==3,d['entropy_worst']==4,d['unsafe_perfect_ignored']==1,d['empty_safe'] is None]
    decision=('PASS_SAFE_PROBE_MINIMAX_VERSION_SPACE_SCOPED' if formal else 'PASS_CONSTRUCTION_ELIGIBLE') if all(gates) else ('FAIL_SAFE_ENVELOPE_ESCAPE' if rnd['unsafe_selected'] else 'FAIL_MINIMAX_SELECTOR')
    return {'task':TASK,'phase':'formal' if formal else 'construction','formal_invocations':1 if formal else 0,'reruns':0,'replacements':0,'tuning':0,'seed':SEED,'decision':decision,'exhaustive_max_n':exhaustive_n,'exhaustive_pair_rows':exrows,'exhaustive_mismatch':exmis,'exhaustive_order_mismatch':exord,'random':rnd,'directed':d}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--random-rows',type=int,default=5000);ap.add_argument('--exhaustive-n',type=int,default=10);ap.add_argument('--out',required=True);a=ap.parse_args()
    r=execute(a.random_rows,a.exhaustive_n);Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
