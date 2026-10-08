from __future__ import annotations
import copy,json
from pathlib import Path
from audit import validate_result_data
HERE=Path(__file__).resolve().parent
base=json.loads((HERE/'FORMAL_RESULT.json').read_text())
mutations=[]
for name,fn in [
 ('valid_count',lambda d:d.__setitem__('valid_exact_equal',99999)),
 ('adversarial_count',lambda d:d.__setitem__('adversarial_exact_equal',49999)),
 ('source_hash',lambda d:d['source_sha256'].__setitem__('oracle.py','0'*64)),
 ('disposition',lambda d:d.__setitem__('disposition','PASS_BUT_WRONG')),
 ('invocation',lambda d:d.__setitem__('formal_reruns',1)),
]:
    d=copy.deepcopy(base); fn(d); errors=validate_result_data(d)
    mutations.append({'mutation':name,'rejected':bool(errors),'errors':errors})
out={'passed':all(x['rejected'] for x in mutations),'controls':mutations}
(HERE/'CORRUPTION_CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
