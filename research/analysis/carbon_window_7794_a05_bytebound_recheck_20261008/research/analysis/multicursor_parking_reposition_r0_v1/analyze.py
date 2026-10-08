from __future__ import annotations
import itertools,json
from pathlib import Path
from model import single_cost,aliased_parked_cost,switch_cost,switch_gain_formula
ROOT=Path(__file__).resolve().parent
POSITIONS=(0,1,2,3)
LENGTHS=range(2,7)
CURSORS=(2,3,4)
SWITCH=(0,1,2,3)

def main():
    sequences=0; alias_checks=0; alias_mismatch=0; switch_checks=0; switch_mismatch=0; strict_gain_cases=0
    by_length={}
    examples={}
    canonical={
      'stationary':(2,2,2,2),
      'alternating_near':(0,1,0,1,0),
      'alternating_far':(0,3,0,3),
      'monotone':(0,1,2,3),
    }
    for n in LENGTHS:
        count=0
        for seq in itertools.product(POSITIONS,repeat=n):
            sequences+=1; count+=1
            base=single_cost(seq)
            for k in CURSORS:
                alias_checks+=1
                if aliased_parked_cost(seq,k)!=base: alias_mismatch+=1
            for s in SWITCH:
                switch_checks+=1
                direct=base-switch_cost(seq,s); formula=switch_gain_formula(seq,s)
                if direct!=formula: switch_mismatch+=1
                if direct>0: strict_gain_cases+=1
        by_length[str(n)]=count
    for name,seq in canonical.items():
        base=single_cost(seq)
        examples[name]={
          'sequence':list(seq),'single':base,
          'aliased_k2':aliased_parked_cost(seq,2),
          'switch':{str(s):switch_cost(seq,s) for s in SWITCH},
          'gain':{str(s):switch_gain_formula(seq,s) for s in SWITCH},
        }
    passed=alias_mismatch==0 and switch_mismatch==0 and strict_gain_cases>0
    out={'task':'MULTICURSOR-PARKING-REPOSITION-R0-20260918-001','formal_invocations':1,'reruns':0,
         'sequences':sequences,'by_length':by_length,'alias_checks':alias_checks,'alias_mismatch':alias_mismatch,
         'switch_checks':switch_checks,'switch_mismatch':switch_mismatch,'strict_gain_cases':strict_gain_cases,
         'examples':examples,'decision':'PASS_MULTICURSOR_PARKING_REPOSITION_SCOPED' if passed else 'FAIL_MULTICURSOR_PARKING_MODEL',
         'pass':passed}
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True));raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
