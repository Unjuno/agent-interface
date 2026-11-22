"""Reconstruct exactly the frozen one-line candidate; never runs the matrix."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / 'FREEZE.json').read_text())
source = ROOT / 'source/doom_typed_observation_v1.py'
assert hashlib.sha256(source.read_bytes()).hexdigest() == freeze['sha256']['source/doom_typed_observation_v1.py']
before = '            abs(elapsed_ms - (ready_ns - capture_ns) / 1e6) > 1e-9):'
after = '            not abs(elapsed_ms - (ready_ns - capture_ns) / 1e6) <= 1e-9):'
text = source.read_text()
if text.count(before) != 1:
    raise ValueError('expected one original predicate')
result = text.replace(before, after).encode()
name = 'candidate/doom_typed_observation_v1.py'
if hashlib.sha256(result).hexdigest() != freeze['sha256'][name]:
    raise ValueError('candidate identity mismatch')
out = ROOT / name
out.parent.mkdir(exist_ok=True)
if out.exists():
    if out.read_bytes() != result:
        raise ValueError('existing candidate differs')
else:
    with out.open('xb') as stream:
        stream.write(result)
print('candidate bytes verified')
