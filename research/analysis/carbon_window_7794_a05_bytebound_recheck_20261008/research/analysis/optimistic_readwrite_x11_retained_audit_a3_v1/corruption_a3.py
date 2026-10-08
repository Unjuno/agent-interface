from __future__ import annotations
import copy,json
from pathlib import Path
from audit_a3 import load_parent,validate,EXPECTED
ROOT=Path(__file__).resolve().parent

def main():
    rows,result,audit,disp,binding=load_parent();tests=[];cases=[]
    x=copy.deepcopy(result);x['gates'].pop('distinct_xids');cases.append(('remove_gate',rows,x,audit,disp,binding))
    x=copy.deepcopy(result);x['gates']['extra_gate']=True;cases.append(('add_gate',rows,x,audit,disp,binding))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='SHARED_GLOBAL_CANDIDATE')['final_effects']['B']='G0';cases.append(('candidate_g0',rr,result,audit,disp,binding))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='SHARED_GLOBAL_SURFACE_ONLY')['final_effects']['B']='G1';cases.append(('erase_surface_discriminator',rr,result,audit,disp,binding))
    rr=copy.deepcopy(rows);next(r for r in rr if r['scenario']=='EXTERNAL_STALE')['b_effect_command_count']=1;cases.append(('stale_effect_command',rr,result,audit,disp,binding))
    bad=list(binding)+['raw_hash'];cases.append(('binding_hash',rows,result,audit,disp,bad))
    for name,rr,res,aa,dd,bb in cases:
        errors,_=validate(rr,res,aa,dd,bb);tests.append({'name':name,'rejected':bool(errors),'errors':errors})
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests}
    (ROOT/'CORRUPTION_A3.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__':main()
