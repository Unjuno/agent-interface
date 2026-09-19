from __future__ import annotations
import copy, json
from pathlib import Path
from audit import independent_expected, validate

ROOT=Path(__file__).resolve().parent

def main():
    base=json.loads((ROOT/'RESULT.json').read_text())
    expected=independent_expected()
    muts=[]
    x=copy.deepcopy(base); x['formal_invocations']=2; muts.append(('invocation',x))
    x=copy.deepcopy(base); x['counts']['candidate_stale_parallel']=1; muts.append(('stale_escape',x))
    x=copy.deepcopy(base); x['counts']['candidate_cross_rw_parallel']=1; muts.append(('rw_escape',x))
    x=copy.deepcopy(base); x['counts']['candidate_ww_parallel']=1; muts.append(('ww_escape',x))
    x=copy.deepcopy(base); x['counts']['write_only_unsafe_parallel']=0; muts.append(('discriminator',x))
    x=copy.deepcopy(base); x['decision']='PASS_FAKE'; muts.append(('decision',x))
    tests=[]
    for name,x in muts:
        errors=validate(x,expected)
        tests.append({'name':name,'rejected':bool(errors),'errors':errors})
    out={'all_rejected':all(t['rejected'] for t in tests),'tests':tests}
    (ROOT/'CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if out['all_rejected'] else 1)

if __name__=='__main__':
    main()
