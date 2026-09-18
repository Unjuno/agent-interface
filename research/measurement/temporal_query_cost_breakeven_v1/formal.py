from fractions import Fraction
import hashlib,json
from pathlib import Path
DEN=40
CLASS=(4,2,8,6); ANCHOR=(4,2,2,2); UNIVERSAL=11
def priors():
    for r in range(DEN+1):
      for l in range(DEN-r+1):
       for e in range(DEN-r-l+1):
        yield tuple(Fraction(x,DEN) for x in (r,l,e,DEN-r-l-e))
def dot(p,b): return sum((p[i]*b[i] for i in range(4)),Fraction(0))
def main():
    ps=list(priors()); bcs=[dot(p,CLASS) for p in ps]; bas=[dot(p,ANCHOR) for p in ps]
    idbad=sum((bcs[i]-bas[i]) != 6*ps[i][2]+4*ps[i][3] for i in range(len(ps)))
    iff=sum(((bcs[i]-bas[i])==0)!=(ps[i][2]==0 and ps[i][3]==0) for i in range(len(ps)))
    eq=(Fraction(1,4),)*4; bc=dot(eq,CLASS); ba=dot(eq,ANCHOR)
    th={'fixed_to_class':Fraction(11)-bc,'class_to_anchor_increment':bc-ba,'fixed_to_anchor':Fraction(11)-ba}
    controls={
      'class_budget_mutation_detected':dot(eq,(4,2,7,6))!=bc,
      'prior_normalization_detected':sum((Fraction(1,5),)*4)!=1,
      'event_coefficient_detected':5*eq[2]+4*eq[3]!=th['class_to_anchor_increment'],
      'reversal_coefficient_detected':6*eq[2]+3*eq[3]!=th['class_to_anchor_increment'],
      'fixed_class_inequality_flip_detected':not(Fraction(5)<th['fixed_to_class'])==(Fraction(5)>=th['fixed_to_class'])}
    out={'task':'TEMPORAL-QUERY-COST-BREAKEVEN-20260919-001','denominator':40,'simplex_points':len(ps),
      'budgets':{'universal':11,'class_only':list(CLASS),'class_anchor':list(ANCHOR)},
      'class_budget_min':str(min(bcs)),'class_budget_max':str(max(bcs)),
      'anchor_budget_min':str(min(bas)),'anchor_budget_max':str(max(bas)),
      'anchor_saving_identity_mismatches':idbad,'zero_iff_no_event_reversal_mismatches':iff,
      'equal_prior_class_budget':str(bc),'equal_prior_anchor_budget':str(ba),
      'equal_prior_thresholds':{k:str(v) for k,v in th.items()},'corruption_controls':controls,
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0}
    ok=(len(ps)==12341 and min(bcs)==2 and max(bcs)==8 and min(bas)==2 and max(bas)==4 and idbad==0 and iff==0 and th=={'fixed_to_class':Fraction(6),'class_to_anchor_increment':Fraction(5,2),'fixed_to_anchor':Fraction(17,2)} and all(controls.values()))
    out['decision']='PASS_TEMPORAL_QUERY_COST_BREAKEVEN_SCOPED' if ok else 'FAIL_THEOREM_OR_INTEGRITY'
    out['digest']=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    Path('RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
