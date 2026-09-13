"""Boundary controls for the OpenTTD v5 proposal schema."""
import json
from pathlib import Path
from openttd_proposal_schema_v5 import parse

valid = [
    {'kind': 'act', 'steps': [
        {'op': 'pointer_move', 'x': 819, 'y': 51},
        {'op': 'dwell_observe', 'delay_ms': 800},
        {'op': 'pointer_drag', 'points': [{'x': 673, 'y': 378}, {'x': 609, 'y': 410}], 'duration_ms': 600},
    ], 'rationale': 'bounded'},
    {'kind': 'verify', 'road_visible': True, 'rationale': 'visible'},
    {'kind': 'stop', 'rationale': 'insufficient evidence'},
]
invalid = [
    {'kind': 'act', 'steps': [], 'rationale': 'empty'},
    {'kind': 'act', 'steps': [{'op': 'pointer_click', 'x': 1280, 'y': 0}], 'rationale': 'outside'},
    {'kind': 'act', 'steps': [{'op': 'dwell_observe', 'delay_ms': 99}], 'rationale': 'short'},
    {'kind': 'act', 'steps': [{'op': 'shell', 'command': 'true'}], 'rationale': 'unsupported'},
    {'kind': 'verify', 'road_visible': 'yes', 'rationale': 'wrong type'},
    {'kind': 'stop', 'rationale': 'x', 'steps': []},
]
for value in valid:
    assert parse(json.dumps(value)) == value
refused = 0
for value in invalid:
    try:
        parse(json.dumps(value))
    except ValueError:
        refused += 1
    else:
        raise AssertionError(value)
report = {'valid': len(valid), 'invalid_refused': refused,
          'limit': 'Tooltip/target-noun meaning is a planner policy, not enforced by this shape schema.'}
out = Path(__file__).resolve().parent / 'results/openttd-proposal-schema-v5.json'
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
