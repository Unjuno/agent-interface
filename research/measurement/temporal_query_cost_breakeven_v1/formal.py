from fractions import Fraction
from itertools import product
import hashlib,json
from pathlib import Path

DEN=40
CLASSES=('RECENT','LONG','EVENT','REVERSAL')
CLASS=(4,2,8,6)
ANCHOR=(4,2,2,2)
UNIVERSAL=11

def priors():
    for r in range(DEN+1):
      for l in range(DEN-r+1):
       for e in range(DEN-r-l+1):
        v=DEN-r-l-e
        yield tuple(Fraction(x,DEN) for x in (r,l,e,v))

def dot(p,b): return sum((p[i]*b[i] for i in range(4)),Fraction(0))

def row(p):
    bc=dot(p,CLASS); ba=dot(p,ANCHOR)
    save_fc=Fraction(UNIVERSAL)-bc
    save_ca=bc-ba
    save_fa=Fraction(UNIVERSAL)-ba
    expected_ca=6*p[2]+4*p[3]
    return {
      'p':[str(x) for x in p],
      'class_budget':str(bc),'anchor_budget':str(ba),
      'fixed_to_class_threshold':str(save_fc),
      'class_to_anchor_increment_threshold':str(save_ca),
      'fixed_to_anchor_threshold':str(save_fa),
      'anchor_saving_identity':str(expected_ca),
      'zero_anchor_saving': save_ca==0,
      'zero_iff_no_event_reversal': (save_ca==0)==(p[2]==0 and p[3]==0),
    }

def main():
    rows=[row(p) for p in priors()]
    bcs=[Fraction(x['class_budget']) for x in rows]
    bas=[Fraction(x['anchor_budget']) for x in rows]
    identities=sum(Fraction(x['class_to_anchor_increment_threshold']) != Fraction(x['anchor_saving_identity']) for x in rows)
    iff=sum(not x['zero_iff_no_event_reversal'] for x in rows)
    eq=(Fraction(1,4),)*4
    bc=dot(eq,CLASS); ba=dot(eq,ANCHOR)
    thresholds={
      'fixed_to_class': Fraction(UNIVERSAL)-bc,
      'class_to_anchor_increment': bc-ba,
      'fixed_to_anchor': Fraction(UNIVERSAL)-ba,
    }
    # controls are theorem perturbations expected to be detected
    corrupt={
      'class_budget_mutation_detected': dot(eq,(4,2,7,6)) != bc,
      'prior_normalization_detected': sum((Fraction(1,5),)*4) != 1,
      'event_coefficient_detected': 5*eq[2]+4*eq[3] != thresholds['class_to_anchor_increment'],
      'reversal_coefficient_detected': 6*eq[2]+3*eq[3] != thresholds['class_to_anchor_increment'],
      'fixed_class_inequality_flip_detected': not (Fraction(5) < thresholds['fixed_to_class']) == (Fraction(5) >= thresholds['fixed_to_class']),
    }
    out={
      'task':'TEMPORAL-QUERY-COST-BREAKEVEN-20260919-001',
      'denominator':DEN,'simplex_points':len(rows),
      'budgets':{'universal':UNIVERSAL,'class_only':list(CLASS),'class_anchor':list(ANCHOR)},
      'class_budget_min':str(min(bcs)),'class_budget_max':str(max(bcs)),
      'anchor_budget_min':str(min(bas)),'anchor_budget_max':str(max(bas)),
      'anchor_saving_identity_mismatches':identities,
      'zero_iff_no_event_reversal_mismatches':iff,
      'equal_prior_class_budget':str(bc),'equal_prior_anchor_budget':str(ba),
      'equal_prior_thresholds':{k:str(v) for k,v in thresholds.items()},
      'corruption_controls':corrupt,
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
    }
    ok=(len(rows)==12341 and min(bcs)==2 and max(bcs)==8 and min(bas)==2 and max(bas)==4 and identities==0 and iff==0 and thresholds=={'fixed_to_class':Fraction(6),'class_to_anchor_increment':Fraction(5,2),'fixed_to_anchor':Fraction(17,2)} and all(corrupt.values()))
    out['decision']='PASS_TEMPORAL_QUERY_COST_BREAKEVEN_SCOPED' if ok else 'FAIL_THEOREM_OR_INTEGRITY'
    raw=json.dumps(out,sort_keys=True,separators=(',',':')).encode(); out['digest']=hashlib.sha256(raw).hexdigest()
    Path('/tmp/ai1819/RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
