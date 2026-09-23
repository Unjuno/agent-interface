"""Offline malformed-plan controls for the OpenTTD model boundary."""
import copy
import hashlib
import json
from pathlib import Path

from openttd_proposal_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/timing-envelope-openttd-schema-01'
R.mkdir(exist_ok=False)
valid = {'kind': 'act', 'steps': [
    {'op': 'pointer_click', 'x': 820, 'y': 51},
    {'op': 'observe'}], 'rationale': 'open road toolbar'}
assert parse(json.dumps(valid)) == valid
invalid = {}
for name, mutate in (
        ('shell_step', lambda row: row['steps'].__setitem__(0, {'op': 'shell'})),
        ('key_step', lambda row: row['steps'].__setitem__(0, {'op': 'key', 'key': 'r'})),
        ('outside', lambda row: row['steps'][0].__setitem__('x', 1024)),
        ('extra_click_field', lambda row: row['steps'][0].__setitem__('button', 1)),
        ('empty_steps', lambda row: row.__setitem__('steps', [])),
        ('string_coordinate', lambda row: row['steps'][0].__setitem__('x', '820')),
        ('verify_string', lambda row: row.update({'kind': 'verify', 'road_visible': 'yes'})),
        ('stop_with_steps', lambda row: row.update({'kind': 'stop'}))):
    candidate = copy.deepcopy(valid)
    mutate(candidate)
    try:
        parse(json.dumps(candidate))
    except ValueError as exc:
        invalid[name] = str(exc)
assert len(invalid) == 8
plan = {'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                    for name in ('openttd_proposal_schema_v1.py',
                                 'probe_openttd_proposal_schema_v1.py')}}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(R / 'invalid.json').write_text(json.dumps(invalid, indent=2) + '\n')
(R / 'result.json').write_text(json.dumps(
    {'valid': 1, 'refused': 8, 'model_calls': 0, 'gui_actions': 0}, indent=2) + '\n')
print(json.dumps({'valid': 1, 'refused': 8}))
