"""Publication-only lossless plan expansion; does not execute any experiment."""
import hashlib, json
from pathlib import Path
root = Path(__file__).resolve().parent
p = json.loads((root / 'plan_compact.json').read_text())
p['cases'] = [dict(id=f'r{r}-{policy}-{s}', rep=r, policy=policy, scenario=s)
              for r, policy, s in p.pop('case_order')]
data = (json.dumps(p, indent=2, sort_keys=True) + '\n').encode()
expected = '2a88f48b54eb4fe83d2e09e21f1206359e57f2da273392e04fdd12ebb11ec0d8'
if hashlib.sha256(data).hexdigest() != expected:
    raise ValueError('reconstructed plan does not match premeasurement freeze')
(root / 'plan.json').write_bytes(data)
print(expected)
