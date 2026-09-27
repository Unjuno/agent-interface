from __future__ import annotations
import copy,json
from pathlib import Path
from audit import validate
ROOT=Path(__file__).resolve().parent

def main():
    rows=json.loads((ROOT/'FORMAL_ROWS.json').read_text());result=json.loads((ROOT/'RESULT.json').read_text());tests=[]
    cases=[]
    x=copy.deepcopy(result);x['formal_invocations']=2;cases.append(('invocation',rows,x))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='INDEPENDENT')['final_effects']['B']='BAD';cases.append(('ind_effect',rr,result))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='SHARED_GLOBAL_CANDIDATE')['final_effects']['B']='G0';cases.append(('candidate_stale',rr,result))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='SHARED_GLOBAL_SURFACE_ONLY')['final_effects']['B']='G1';cases.append(('erase_discriminator',rr,result))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='EXTERNAL_STALE')['b_effect_command_count']=1;cases.append(('stale_effect_command',rr,result))
    x=copy.deepcopy(result);x['decision']='PASS_FAKE';cases.append(('decision',rows,x))
    for name,rr,res in cases:
        errors=validate(rr,res);tests.append({'name':name,'rejected':bool(errors),'errors':errors})
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests}
    (ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__':main()
