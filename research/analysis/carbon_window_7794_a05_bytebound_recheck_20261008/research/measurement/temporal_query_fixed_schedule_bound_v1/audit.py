from fractions import Fraction
from itertools import combinations
import argparse,hashlib,json,math
from pathlib import Path
GRID=tuple(range(0,1001,25)); ANCHORS=tuple(range(250,826,25)); BUDGET=4

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def score(s):
    r=int(sum(900<=t<=1000 for t in s)>=4)
    l=int(any(t<=300 for t in s) and any(t>=900 for t in s))
    e=Fraction(sum(any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s) for a in ANCHORS),len(ANCHORS))
    v=Fraction(sum(any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s) for a in ANCHORS),len(ANCHORS))
    return (Fraction(r),Fraction(l),e,v)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);assert not out.exists();r=json.loads(Path(a.result).read_text());f=json.loads(Path(a.freeze).read_text())
    best=Fraction(-1); bests=[]; allpos=0; maxmin=Fraction(-1)
    n=0
    for s in combinations(GRID,BUDGET):
        n+=1; vals=score(s); av=sum(vals,Fraction(0))/4; mn=min(vals)
        allpos+=int(all(x>0 for x in vals));
        if av>best:best=av;bests=[s]
        elif av==best:bests.append(s)
        if mn>maxmin:maxmin=mn
    checks={
      'count':n==101270==r['schedule_count']==r['expected_full_schedule_count'],
      'best':(best.numerator,best.denominator)==(r['best_fixed_score_num'],r['best_fixed_score_den']),
      'best_witness_count':len(bests)==r['best_witness_count'],
      'all_positive_zero':allpos==0==r['all_classes_positive_schedule_count'],
      'minimax_zero':maxmin==0==Fraction(r['max_min_score_num'],r['max_min_score_den']),
      'strict_bound':best<1,
      'query_constructive':r['query_constructive_all_pass'] and r['query_constructive_case_count']==50,
      'symbolic':r['symbolic']['mutually_incompatible'] is True,
      'formal':r['formal_invocations']==1 and r['reruns']==0,
      'source_analyze':h('analyze.py')==f['sha256']['analyze.py'],
      'source_audit':h('audit.py')==f['sha256']['audit.py'],
      'source_plan':h('PLAN.md')==f['sha256']['PLAN.md']
    }
    decision='PASS_TEMPORAL_FIXED_SCHEDULE_ANALYTIC_BOUND_SCOPED' if all(checks.values()) else 'FAIL_INTEGRITY'
    z={'status':'PASS' if all(checks.values()) else 'FAIL','decision':decision,'checks':checks,'oracle_best_fraction':f'{best.numerator}/{best.denominator}','oracle_best_float':float(best),'oracle_best_witness_count':len(bests),'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)}
    out.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
