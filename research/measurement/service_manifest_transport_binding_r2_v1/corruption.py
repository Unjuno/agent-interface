from __future__ import annotations
import copy,json
from pathlib import Path
from audit import validate
ROOT=Path(__file__).resolve().parent

def main():
    r=json.loads((ROOT/'RESULT.json').read_text()); tests=[]
    muts=[]
    x=copy.deepcopy(r);x['formal_invocations']=2;muts.append(('invocation',x))
    x=copy.deepcopy(r);x['candidate_oracle_mismatch']=1;muts.append(('oracle',x))
    x=copy.deepcopy(r);x['logical_binding']['invalid_binding_authorizations']=1;muts.append(('binding_escape',x))
    x=copy.deepcopy(r);x['inline_cached']['stale_endpoint_selections']=0;muts.append(('cached_discriminator',x))
    x=copy.deepcopy(r);x['inline_refreshed']['manifest_hash_changes']-=1;muts.append(('refreshed_count',x))
    x=copy.deepcopy(r);x['decision']='PASS_FAKE';muts.append(('decision',x))
    for name,x in muts:
        errs=validate(x); tests.append({'name':name,'rejected':bool(errs),'errors':errs})
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests}
    (ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__':main()
