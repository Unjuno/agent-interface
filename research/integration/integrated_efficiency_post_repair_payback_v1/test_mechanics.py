import json
from decimal import Decimal
from pathlib import Path
from common import validate_fixture, compute
ROOT=Path(__file__).resolve().parent
f=json.loads((ROOT/'fixture.json').read_text())
assert validate_fixture(f)
p,e,d,r=compute(f)
assert p['elapsed_ms'] == Decimal('24874.512215')
assert e['elapsed_ms'] == Decimal('37921.563313')
assert p['input_tokens'] == 9299 and e['input_tokens'] == 27906
assert p['planner_generations'] == 1 and e['planner_generations'] == 3
assert p['model_visible_images'] == 1 and e['model_visible_images'] == 3
assert p['local_observations'] == 68 and e['local_observations'] == 65
assert p['durable_calls'] == 58 and e['durable_calls'] == 48
print('mechanics PASS')
