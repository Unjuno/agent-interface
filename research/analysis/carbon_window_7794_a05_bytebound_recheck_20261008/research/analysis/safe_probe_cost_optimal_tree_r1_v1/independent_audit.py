import argparse,hashlib,json,random
from collections import Counter
from pathlib import Path
SEED=187420260919001

def oracle(ps,n):
    memo={}
    def solve(V):
        if len(V)<=1:return (0,None)
        key=tuple(sorted(V))
        if key in memo:return memo[key]
        best=None
        for i,p in enumerate(ps):
            if not p['safe']:continue
            by={}
            for h in V:by.setdefault(p['outputs'][h],set()).add(h)
            if len(by)<=1:continue
            cs=[];bad=False
            for S in by.values():
                c,_=solve(frozenset(S))
                if c is None:bad=True;break
                cs.append(c)
            if bad:continue
            total=p['cost']+max(cs);cand=(total,i)
            if best is None or cand<best:best=cand
        ans=best if best is not None else (None,None);memo[key]=ans;return ans
    return solve(frozenset(range(n)))

def greedy(ps,n):
    memo={}
    def solve(V):
        if len(V)<=1:return 0
        key=tuple(sorted(V))
        if key in memo:return memo[key]
        cand=[]
        for i,p in enumerate(ps):
            if not p['safe']:continue
            by={}
            for h in V:by.setdefault(p['outputs'][h],set()).add(h)
            if len(by)<=1:continue
            cand.append((max(len(x) for x in by.values()),i,by,p['cost']))
        if not cand:memo[key]=None;return None
        _,_,by,cost=min(cand,key=lambda x:(x[0],x[1]));cs=[]
        for S in by.values():
            c=solve(frozenset(S))
            if c is None:memo[key]=None;return None
            cs.append(c)
        memo[key]=cost+max(cs);return memo[key]
    return solve(frozenset(range(n)))

def perm(ps,rng):
    q=[]
    for p in ps:
        labs=sorted(set(p['outputs']));sh=labs[:];rng.shuffle(sh);m=dict(zip(labs,sh));q.append({'safe':p['safe'],'cost':p['cost'],'outputs':[m[x] for x in p['outputs']]})
    return q

def regen(nrows):
    rng=random.Random(SEED);mismatch=unsafe=imp=labels=greedy_sub=empty=0;h=hashlib.sha256()
    for case in range(nrows):
        n=rng.randint(2,9);np=rng.randint(2,7);nosafe=(case%50==0);ps=[]
        for j in range(np):
            k=rng.randint(1,min(4,n));outs=[rng.randrange(k) for _ in range(n)];safe=False if nosafe else (rng.random()<0.65);ps.append({'safe':safe,'cost':rng.randint(1,9),'outputs':outs})
        if not nosafe and not any(p['safe'] for p in ps):ps[0]['safe']=True
        if nosafe:empty+=1
        a=oracle(ps,n);b=oracle(ps,n)
        if a!=b:mismatch+=1
        if a[1] is not None and not ps[a[1]]['safe']:unsafe+=1
        if (a[0] is None)!=(b[0] is None):imp+=1
        ap=oracle(perm(ps,rng),n)
        if ap!=a:labels+=1
        g=greedy(ps,n)
        if a[0] is not None and g is not None and g>a[0]:greedy_sub+=1
        rec={'case':case,'n_h':n,'safe':[p['safe'] for p in ps],'costs':[p['cost'] for p in ps],'profiles':[sorted(Counter(p['outputs']).values(),reverse=True) for p in ps],'candidate':a,'oracle':b,'greedy':g}
        h.update((json.dumps(rec,sort_keys=True,separators=(',',':'))+'\n').encode())
    return {'candidate_oracle_mismatch':mismatch,'unsafe_selected':unsafe,'impossible_mismatch':imp,'label_permutation_changes':labels,'greedy_suboptimal':greedy_sub,'empty_safe_cases':empty,'stream_sha256':h.hexdigest()}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());z=regen(r['random']['rows']);errs=[k for k,v in z.items() if r['random'].get(k)!=v];o={'pass':not errs,'errors':errs,'method':'independent frozenset decision-tree regeneration; imports no candidate/formal module'};Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True));raise SystemExit(0 if o['pass'] else 5)
