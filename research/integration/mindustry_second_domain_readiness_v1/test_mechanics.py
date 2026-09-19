import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
f=json.loads((ROOT/'fixture.json').read_text())
assert len(f['cells'])==14
assert [c['id'] for c in f['cells']]==list(range(1,15))
assert [c['id'] for c in f['cells'] if not c['passed']]==[9,11,12,13]
assert all(c['passed'] for c in f['cells'] if c['id'] in {1,2,3,4,5,6,7,8,10,14})
assert len(f['sources'])==8
print('PASS mechanics: 14 cells; missing 9,11,12,13; source refs 8')
