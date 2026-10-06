"""Six effective well-formed mutations of saved observations; no native runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from audit import audit


def controls(rows,root):
    base=audit(rows,root)
    if base['errors']:raise ValueError('intact evidence must pass first')
    results=[]
    for kind in ('shift_bit','b_mask','source_hash','exit_code','missing_case','query_order'):
        edited=deepcopy(rows)
        r=next(r for r in edited if r['condition']=='SHIFT_SAME' and r['variant']=='proposal')
        if kind=='shift_bit':
            code=r['keycodes']['SHIFT'];r['steps'][2]['keymap'][code//8]^=1<<(code%8)
        elif kind=='b_mask':
            for step in r['steps'][3:]:
                for e in step['app']['events']:
                    if e['keycode']==r['keycodes']['b']:e['state']^=1
        elif kind=='source_hash':r['backend_sha256']='0'*64
        elif kind=='exit_code':r['exits'][0]['returncode']=1
        elif kind=='missing_case':edited.pop()
        elif kind=='query_order':r['steps'][2]['query_ended_ns']=r['steps'][2]['query_started_ns']-1
        raw=json.dumps(edited,sort_keys=True,separators=(',',':')).encode()
        result=audit(edited,root)
        results.append(dict(mutation=kind,effective=edited!=rows,rejected=bool(result['errors']),
                            errors=result['errors'],mutated_sha256=hashlib.sha256(raw).hexdigest()))
    return dict(intact_errors=base['errors'],controls=results,
                passed=all(x['effective'] and x['rejected'] for x in results))

if __name__=='__main__':
    result=controls(json.loads(Path(sys.argv[1]).read_text()),Path(__file__).resolve().parent)
    print(json.dumps(result,sort_keys=True,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
