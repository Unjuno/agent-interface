from fractions import Fraction as F
from itertools import product
import argparse,hashlib,json
from pathlib import Path
VALUES=tuple(F(i,2) for i in range(0,17)); C_VALUES=tuple(F(i,4) for i in range(1,17)); H_VALUES=tuple(F(i,4) for i in range(0,65))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def direct(f,q,x): return 'QUERY_CHEAPER' if x+q<f else ('FIXED_CHEAPER' if x+q>f else 'TIE')
def pclass(f,q):
    if all(b<=a for a,b in zip(f,q)) and any(b<a for a,b in zip(f,q)):return 'QUERY_PARETO_DOMINATES'
    if all(a<=b for a,b in zip(f,q)) and any(a<b for a,b in zip(f,q)):return 'FIXED_PARETO_DOMINATES'
    if f==q:return 'TIE'
    return 'TRADEOFF'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();r=json.loads(Path(a.result).read_text());f=json.loads(Path(a.freeze).read_text())
    fc={'QUERY_CHEAPER':0,'FIXED_CHEAPER':0,'TIE':0}; rows=0
    for x,y,z in product(VALUES,repeat=3):fc[direct(x,y,z)]+=1;rows+=1
    linear_bad=0;linear_rows=0
    for k,c,hv in product(range(1,5),C_VALUES,H_VALUES):
        threshold=(11-k)*c; got='QUERY_CHEAPER' if hv<threshold else ('FIXED_CHEAPER' if hv>threshold else 'TIE'); exp=direct(11*c,k*c,hv);linear_bad+=int(got!=exp);linear_rows+=1
    pcs=[(((F(10),F(5)),(F(8),F(4))),'QUERY_PARETO_DOMINATES'),(((F(8),F(4)),(F(10),F(5))),'FIXED_PARETO_DOMINATES'),(((F(8),F(6)),(F(7),F(7))),'TRADEOFF'),(((F(8),F(6)),(F(8),F(6))),'TIE')]
    checks={
      'decision':r['decision']=='PASS_TEMPORAL_SAMPLE_COST_NOT_IDENTIFIABLE_FROM_COUNT_SCOPED',
      'opposite_orders':set(r['directed_results'].values())=={'QUERY_CHEAPER','FIXED_CHEAPER','TIE'},
      'count_only':r['count_only_ordering']=='NOT_IDENTIFIABLE',
      'frontier_rows':r['frontier_rows']==rows,
      'frontier_counts':r['frontier_counts']==fc,
      'frontier_mismatch':r['frontier_mismatch']==0,
      'linear_rows':r['linear_rows']==linear_rows and r['linear_mismatch']==0 and linear_bad==0,
      'k4_threshold':r['k4_threshold_ratio_values']==['7/1'] and r['k4_threshold_exact']=='7*c',
      'pareto':r['pareto_mismatch']==0 and all(pclass(*pair)==exp for pair,exp in pcs),
      'scalarization_rejected':r['scalarization_without_weights']=='REJECTED',
      'corruptions':all(r['corruption_controls'].values()),
      'formal':r['formal_invocations']==1 and r['reruns']==0 and r['replacements']==0 and r['tuning']==0,
      'source_plan':h('PLAN.md')==f['sha256']['PLAN.md'],
      'source_analyze':h('analyze.py')==f['sha256']['analyze.py'],
      'source_audit':h('audit.py')==f['sha256']['audit.py'],
    }
    z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
