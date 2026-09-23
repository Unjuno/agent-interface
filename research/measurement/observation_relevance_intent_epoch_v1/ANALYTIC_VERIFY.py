from __future__ import annotations
import json, argparse
from pathlib import Path

def verify():
    A=frozenset({1,17}); B=frozenset({33,49}); x=33
    relevance_only_input=('s0',1,tuple(sorted(A)),(x,),())
    w0_input=relevance_only_input
    w1_input=relevance_only_input
    same_inputs=(w0_input==w1_input)
    required={'W0':'SUPPRESS','W1':'FORWARD'}
    deterministic_outputs=['SUPPRESS','FORWARD']
    rows=[]
    for output in deterministic_outputs:
        rows.append({
            'output_for_identical_input':output,
            'satisfies_W0_nontrivial_suppression': output==required['W0'],
            'satisfies_W1_safety': output==required['W1'],
            'satisfies_both': output==required['W0'] and output==required['W1'],
        })
    return {
      'assumption_async_intent_before_relevance_publication':True,
      'relevance_only_inputs_identical':same_inputs,
      'x_outside_old_A':x not in A,
      'x_inside_new_B':x in B,
      'required_decisions':required,
      'deterministic_output_cases':rows,
      'exists_relevance_only_output_satisfying_both':any(r['satisfies_both'] for r in rows),
      'necessity_claim':'additional intent/currentness discriminator OR atomic intent+relevance publication is necessary for useful W0 suppression and W1 safety',
      'pass': same_inputs and x not in A and x in B and not any(r['satisfies_both'] for r in rows),
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out');a=ap.parse_args()
    r=verify();s=json.dumps(r,indent=2,sort_keys=True)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s)
    raise SystemExit(0 if r['pass'] else 4)
if __name__=='__main__':main()
