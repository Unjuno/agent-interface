from __future__ import annotations
import argparse, hashlib, json, random
from functools import lru_cache
from pathlib import Path

TASK='SAFE-PROBE-COST-OPTIMAL-TREE-R1-20260919-001'
SEED=187420260919001
INF=None

def groups_for_probe_mask(probe, mask, n_h):
    g={}
    outs=probe['outputs']
    for h in range(n_h):
        if mask & (1<<h):
            g.setdefault(outs[h],0)
            g[outs[h]] |= (1<<h)
    return tuple(g.values())

def candidate(probes, n_h):
    full=(1<<n_h)-1
    @lru_cache(None)
    def solve(mask):
        if mask & (mask-1)==0:
            return (0,None)
        best=None
        for i,p in enumerate(probes):
            if not p['safe']:
                continue
            cells=groups_for_probe_mask(p,mask,n_h)
            if len(cells)<=1:
                continue
            child=[]; impossible=False
            for cell in cells:
                cc,_=solve(cell)
                if cc is None:
                    impossible=True; break
                child.append(cc)
            if impossible:
                continue
            total=p['cost']+max(child)
            key=(total,i)
            if best is None or key < best[0]:
                best=(key,(total,i))
        return best[1] if best is not None else (None,None)
    return solve(full)

def oracle(probes, n_h):
    full=frozenset(range(n_h))
    memo={}
    def solve(V):
        if len(V)<=1:
            return (0,None)
        if V in memo:
            return memo[V]
        best=None
        for i,p in enumerate(probes):
            if not p['safe']:
                continue
            by={}
            for h in V:
                by.setdefault(p['outputs'][h],set()).add(h)
            if len(by)<=1:
                continue
            costs=[]; bad=False
            for cell in by.values():
                cc,_=solve(frozenset(cell))
                if cc is None:
                    bad=True; break
                costs.append(cc)
            if bad:
                continue
            total=p['cost']+max(costs)
            key=(total,i)
            if best is None or key<best[0]:
                best=(key,(total,i))
        ans=best[1] if best is not None else (None,None)
        memo[V]=ans
        return ans
    return solve(full)

def greedy(probes,n_h):
    full=(1<<n_h)-1
    memo={}
    def solve(mask):
        if mask & (mask-1)==0:
            return 0
        if mask in memo:
            return memo[mask]
        candidates=[]
        for i,p in enumerate(probes):
            if not p['safe']:
                continue
            cells=groups_for_probe_mask(p,mask,n_h)
            if len(cells)<=1:
                continue
            candidates.append((max(c.bit_count() for c in cells),i,cells,p['cost']))
        if not candidates:
            memo[mask]=None; return None
        _,i,cells,cost=min(candidates,key=lambda x:(x[0],x[1]))
        child=[]
        for cell in cells:
            cc=solve(cell)
            if cc is None:
                memo[mask]=None; return None
            child.append(cc)
        memo[mask]=cost+max(child)
        return memo[mask]
    return solve(full)

def permute_labels(probes,rng):
    q=[]
    for p in probes:
        labs=sorted(set(p['outputs'])); sh=labs[:]; rng.shuffle(sh); mp=dict(zip(labs,sh))
        q.append({'safe':p['safe'],'cost':p['cost'],'outputs':[mp[x] for x in p['outputs']]})
    return q

def directed():
    perfect={'safe':True,'cost':10,'outputs':[0,1,2,3]}
    b1={'safe':True,'cost':1,'outputs':[0,0,1,1]}
    b2={'safe':True,'cost':1,'outputs':[0,1,0,1]}
    unsafe={'safe':False,'cost':0,'outputs':[0,1,2,3]}
    noinfo={'safe':True,'cost':1,'outputs':[0,0,0,0]}
    return {
      'expensive_perfect':{'optimal':candidate([perfect,b1,b2],4),'oracle':oracle([perfect,b1,b2],4),'greedy_cost':greedy([perfect,b1,b2],4)},
      'unsafe_perfect':{'optimal':candidate([unsafe,b1,b2],4),'oracle':oracle([unsafe,b1,b2],4)},
      'impossible':{'optimal':candidate([b1],4),'oracle':oracle([b1],4)},
      'noinfo':{'optimal':candidate([noinfo,b1,b2],4),'oracle':oracle([noinfo,b1,b2],4)},
    }

def exhaustive():
    rows=mismatch=unsafe_sel=impossible_mismatch=0
    for n_h in range(2,5):
        nmaps=1<<n_h
        for m0 in range(nmaps):
            out0=[(m0>>h)&1 for h in range(n_h)]
            for m1 in range(nmaps):
                out1=[(m1>>h)&1 for h in range(n_h)]
                for sf in range(4):
                    safe0=bool(sf&1);safe1=bool(sf&2)
                    for c0 in (1,2,3):
                        for c1 in (1,2,3):
                            probes=[{'safe':safe0,'cost':c0,'outputs':out0},{'safe':safe1,'cost':c1,'outputs':out1}]
                            a=candidate(probes,n_h);b=oracle(probes,n_h);rows+=1
                            if a!=b:mismatch+=1
                            if (a[0] is None)!=(b[0] is None): impossible_mismatch+=1
                            if a[1] is not None and not probes[a[1]]['safe']:unsafe_sel+=1
    return {'rows':rows,'candidate_oracle_mismatch':mismatch,'unsafe_selected':unsafe_sel,'impossible_mismatch':impossible_mismatch}

def random_block(nrows):
    rng=random.Random(SEED)
    mismatch=unsafe_sel=impossible_mismatch=label_change=greedy_suboptimal=0
    stream=hashlib.sha256();examples=[];empty_safe=0
    for case in range(nrows):
        n_h=rng.randint(2,9);n_p=rng.randint(2,7);no_safe=(case%50==0);probes=[]
        for j in range(n_p):
            k=rng.randint(1,min(4,n_h));outs=[rng.randrange(k) for _ in range(n_h)]
            safe=False if no_safe else (rng.random()<0.65)
            probes.append({'safe':safe,'cost':rng.randint(1,9),'outputs':outs})
        if not no_safe and not any(p['safe'] for p in probes):probes[0]['safe']=True
        if no_safe:empty_safe+=1
        a=candidate(probes,n_h);b=oracle(probes,n_h)
        if a!=b:mismatch+=1
        if (a[0] is None)!=(b[0] is None):impossible_mismatch+=1
        if a[1] is not None and not probes[a[1]]['safe']:unsafe_sel+=1
        q=permute_labels(probes,rng);ap=candidate(q,n_h)
        if ap!=a:label_change+=1
        g=greedy(probes,n_h)
        if a[0] is not None and g is not None and g>a[0]:
            greedy_suboptimal+=1
            if len(examples)<5:
                examples.append({'case':case,'optimal_cost':a[0],'optimal_first':a[1],'greedy_cost':g,'probe_costs':[p['cost'] for p in probes],'safe':[p['safe'] for p in probes]})
        rec={'case':case,'n_h':n_h,'safe':[p['safe'] for p in probes],'costs':[p['cost'] for p in probes],'profiles':[sorted(__import__('collections').Counter(p['outputs']).values(),reverse=True) for p in probes],'candidate':a,'oracle':b,'greedy':g}
        stream.update((json.dumps(rec,sort_keys=True,separators=(',',':'))+'\n').encode())
    return {'rows':nrows,'candidate_oracle_mismatch':mismatch,'unsafe_selected':unsafe_sel,'impossible_mismatch':impossible_mismatch,'label_permutation_changes':label_change,'greedy_suboptimal':greedy_suboptimal,'empty_safe_cases':empty_safe,'examples':examples,'stream_sha256':stream.hexdigest()}

def execute(random_rows):
    ex=exhaustive();rnd=random_block(random_rows);d=directed();formal=(random_rows==100000)
    gates=[ex['rows']==12096,ex['candidate_oracle_mismatch']==0,ex['unsafe_selected']==0,ex['impossible_mismatch']==0,rnd['candidate_oracle_mismatch']==0,rnd['unsafe_selected']==0,rnd['impossible_mismatch']==0,rnd['label_permutation_changes']==0,rnd['greedy_suboptimal']>0,d['expensive_perfect']['optimal']==(2,1),d['expensive_perfect']['oracle']==(2,1),d['expensive_perfect']['greedy_cost']==10,d['unsafe_perfect']['optimal']==(2,1),d['impossible']['optimal']==(None,None),d['noinfo']['optimal']==(2,1)]
    decision=('PASS_SAFE_PROBE_COST_OPTIMAL_TREE_SCOPED' if formal else 'PASS_CONSTRUCTION_ELIGIBLE') if all(gates) else ('FAIL_SAFE_ENVELOPE_ESCAPE' if ex['unsafe_selected'] or rnd['unsafe_selected'] else 'FAIL_COST_OPTIMALITY')
    return {'task':TASK,'phase':'formal' if formal else 'construction','formal_invocations':1 if formal else 0,'reruns':0,'replacements':0,'tuning':0,'seed':SEED,'decision':decision,'exhaustive':ex,'random':rnd,'directed':d}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--random-rows',type=int,default=5000);ap.add_argument('--out',required=True);a=ap.parse_args()
    r=execute(a.random_rows);Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
