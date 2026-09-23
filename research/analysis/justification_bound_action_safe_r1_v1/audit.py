from itertools import combinations,product
import argparse,json,hashlib
from pathlib import Path
S=('B0','B1','B2');JS=tuple([(x,) for x in S]+list(combinations(S,2)));ST=('SAME_FALSE','SAME_TRUE','CHANGED_FALSE','CHANGED_TRUE')
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def val(x):return x.endswith('TRUE')
def same(x):return x.startswith('SAME_')
def fams():
 for m in range(1,1<<len(JS)):yield tuple(JS[i] for i in range(len(JS)) if m>>i&1)
def sat(j,v):return all(v[x] for x in j)
def rec(f,m):
 v={b:bool(m>>i&1) for i,b in enumerate(S)};return tuple(j for j in f if sat(j,v))
def oracle(r,c):return any(all(same(c[x]) and val(c[x]) for x in j) for j in r)
def current(f,c):return any(all(val(c[x]) for x in j) for j in f)
def allsup(r,c):
 u={x for j in r for x in j};return bool(r) and all(same(c[x]) and val(c[x]) for x in u)
def counts():
 st={'families':0,'rows':0,'mismatch':0,'candidate_safe':0,'stale_all_committed_safe':0,'newly_true_uncommitted_safe':0,'surviving_committed_alt_safe':0,'sticky_unsafe':0,'current_truth_only_unsafe':0,'all_support_false_reject':0,'safe_without_witness':0}
 for f in fams():
  st['families']+=1
  for m in range(8):
   r=rec(f,m)
   if not r:continue
   for ss in product(ST,repeat=3):
    c=dict(zip(S,ss));alive=[j for j in r if all(same(c[x]) and val(c[x]) for x in j)];o=bool(alive);st['rows']+=1;st['candidate_safe']+=int(o);st['safe_without_witness']+=0
    if not alive:st['sticky_unsafe']+=1
    if current(f,c) and not alive:st['current_truth_only_unsafe']+=1
    newly=[j for j in f if j not in r and all(val(c[x]) for x in j)]
    if newly and not alive:st['newly_true_uncommitted_safe']+=0
    if alive and any(j not in alive for j in r):st['surviving_committed_alt_safe']+=1;st['all_support_false_reject']+=int(not allsup(r,c))
 return st
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());F=json.loads(Path(a.freeze).read_text());Sx=counts();checks={'decision':R['decision']=='PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED','stats':R['stats']==Sx,'mismatch':R['stats']['mismatch']==0,'stale':R['stats']['stale_all_committed_safe']==0,'newly':R['stats']['newly_true_uncommitted_safe']==0,'survive':R['stats']['surviving_committed_alt_safe']>0,'sticky':R['stats']['sticky_unsafe']>0,'truth_only':R['stats']['current_truth_only_unsafe']>0,'overinvalid':R['stats']['all_support_false_reject']>0,'witness':R['stats']['safe_without_witness']==0,'directed':all(R['directed'].values()),'corruptions':all(R['corruptions'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_formal':h('formal.py')==F['sha256']['formal.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']};z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
