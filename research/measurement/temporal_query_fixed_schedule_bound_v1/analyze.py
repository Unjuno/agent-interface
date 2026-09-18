from fractions import Fraction
from itertools import combinations
import hashlib,json,math,argparse
from pathlib import Path
GRID=tuple(range(0,1001,25)); ANCHORS=tuple(range(250,826,25)); BUDGET=4

def recent(s): return int(sum(900<=t<=1000 for t in s)>=4)
def longb(s): return int(any(t<=300 for t in s) and any(t>=900 for t in s))
def event_num(s): return sum(any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s) for a in ANCHORS)
def rev_num(s): return sum(any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s) for a in ANCHORS)
def score_tuple(s): return (Fraction(recent(s),1),Fraction(longb(s),1),Fraction(event_num(s),len(ANCHORS)),Fraction(rev_num(s),len(ANCHORS)))
def avg(vals): return sum(vals,Fraction(0,1))/4

def query_witnesses():
    out={'RECENT_DENSE':(925,950,975,1000),'LONG_BASELINE':(300,400,900,1000)}
    for a in ANCHORS:
        out[f'EVENT_CENTERED:{a}']=(a-75,a-25,a+25,a+75)
        out[f'REVERSAL_BRACKET:{a}']=(a-125,a-25,a+25,a+125)
    for k,s in out.items():
        assert len(s)<=BUDGET and all(t in GRID for t in s)
        if k=='RECENT_DENSE': assert recent(s)
        elif k=='LONG_BASELINE': assert longb(s)
        elif k.startswith('EVENT'): assert event_num_for_anchor(s,int(k.split(':')[1]))
        else: assert rev_num_for_anchor(s,int(k.split(':')[1]))
    return out

def event_num_for_anchor(s,a): return int(any(a-100<=t<a for t in s) and any(a<t<=a+100 for t in s))
def rev_num_for_anchor(s,a): return int(any(a-150<=t<=a-25 for t in s) and any(a+25<=t<=a+150 for t in s))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--construction',action='store_true'); a=ap.parse_args(); p=Path(a.output); assert not p.exists()
    symbolic = {'budget':BUDGET,'recent_requires_recent_count':4,'long_requires_old_outside_recent':True,'mutually_incompatible':True}
    schedules=list(combinations(GRID,BUDGET)) if not a.construction else list(combinations(GRID[:17],BUDGET))
    best_score=Fraction(-1,1); best=[]; max_min=Fraction(-1,1); max_min_sched=[]; count_all_positive=0
    for s in schedules:
        vals=score_tuple(s); sc=avg(vals); mn=min(vals)
        if all(v>0 for v in vals): count_all_positive+=1
        if sc>best_score: best_score=sc; best=[s]
        elif sc==best_score: best.append(s)
        if mn>max_min: max_min=mn; max_min_sched=[s]
        elif mn==max_min: max_min_sched.append(s)
    q=query_witnesses()
    result={
      'construction':a.construction,'grid':list(GRID),'anchors':list(ANCHORS),'budget':BUDGET,
      'schedule_count':len(schedules),'expected_full_schedule_count':math.comb(len(GRID),BUDGET),
      'symbolic':symbolic,'best_fixed_score_num':best_score.numerator,'best_fixed_score_den':best_score.denominator,
      'best_fixed_score_float':float(best_score),'best_witnesses':[list(x) for x in best[:50]],'best_witness_count':len(best),
      'max_min_score_num':max_min.numerator,'max_min_score_den':max_min.denominator,'all_classes_positive_schedule_count':count_all_positive,
      'query_constructive_case_count':len(q),'query_constructive_all_pass':True,'formal_invocations':0 if a.construction else 1,'reruns':0
    }
    raw=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['digest']=hashlib.sha256(raw).hexdigest()
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
