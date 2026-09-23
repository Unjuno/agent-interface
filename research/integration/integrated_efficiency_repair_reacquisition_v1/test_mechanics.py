#!/usr/bin/env python3
import json
from pathlib import Path
from common import validate_fixture, compute, ms_to_ns
R=Path(__file__).resolve().parent
f=json.loads((R/'fixture.json').read_text())
assert validate_fixture(f)
assert ms_to_ns('12341.465157') == 12341465157
x=compute(f)
assert x['planner_generations']['numerator']==1 and x['planner_generations']['denominator']==1
assert x['model_visible_images']['numerator']==1 and x['model_visible_images']['denominator']==1
assert not (R/'RESULT.json').exists()
print('PASS mechanics')
