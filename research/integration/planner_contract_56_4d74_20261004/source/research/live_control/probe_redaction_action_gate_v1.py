"""Offline refusal controls for redaction-aware action admission."""
import hashlib
import json
from pathlib import Path

from redaction_action_gate_v1 import authorize, intersects
from redaction_action_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/redaction-action-controls-01'
R.mkdir(exist_ok=False)


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = ['probe_redaction_action_gate_v1.py', 'redaction_action_gate_v1.py',
         'redaction_action_schema_v1.py']
dump('plan.json', {
    'scope': 'offline proposal/schema/geometry refusals; no model or GUI',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})

click = parse('{"kind":"click","x":270,"y":277,"rationale":"visible Save"}')
common = dict(allowed_target_box=[248, 264, 295, 291],
              private_redacted_boxes=[[60, 264, 248, 291]],
              observation_id='current', current_observation_id='current')
allowed = authorize(click, **common)
assert allowed['authorized'] is True
assert not intersects(common['allowed_target_box'], common['private_redacted_boxes'][0])

refusals = []
cases = [
    ('inside-redaction', {'kind': 'click', 'x': 100, 'y': 277, 'rationale': 'bad'}, common,
     'point_inside_redacted_region'),
    ('outside-target', {'kind': 'click', 'x': 400, 'y': 277, 'rationale': 'bad'}, common,
     'point_outside_declared_target'),
    ('stale-observation', click, dict(common, current_observation_id='new'),
     'observation_identity_mismatch'),
    ('planner-stop', {'kind': 'stop', 'reason': 'unknown'}, common,
     'planner_requested_stop'),
    ('overlap', click, dict(common, allowed_target_box=[247, 264, 295, 291]),
     'target_evidence_intersects_redaction'),
]
for label, proposal, kwargs, reason in cases:
    result = authorize(proposal, **kwargs)
    assert result == {'authorized': False, 'reason': reason}
    refusals.append({'case': label, 'reason': reason})

bad = [
    '{}', '{"kind":"click","x":270,"y":277}',
    '{"kind":"click","x":270.0,"y":277,"rationale":"bad"}',
    '{"kind":"stop","reason":""}',
    '{"kind":"write","x":100,"y":277,"rationale":"bad"}',
]
schema_refusals = []
for index, text in enumerate(bad):
    try:
        parse(text)
    except ValueError as exc:
        schema_refusals.append({'index': index, 'error': str(exc)})
    else:
        raise AssertionError('invalid model proposal accepted')

result = {'allowed_disjoint_clicks': 1, 'action_refusals': len(refusals),
          'schema_refusals': len(schema_refusals), 'model_calls': 0,
          'gui_actions': 0}
dump('refusals.json', refusals + schema_refusals)
dump('result.json', result)
print(json.dumps(result, indent=2))
