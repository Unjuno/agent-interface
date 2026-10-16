"""Offline controls for field-mutation redaction admission."""
import hashlib
import json
from pathlib import Path

from redaction_mutation_gate_v1 import authorize
from redaction_mutation_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/redaction-mutation-controls-01'
R.mkdir(exist_ok=False)
names = ['probe_redaction_mutation_gate_v1.py', 'redaction_mutation_gate_v1.py',
         'redaction_mutation_schema_v1.py', 'redaction_action_gate_v1.py']
(R / 'plan.json').write_text(json.dumps({
    'scope': 'offline mutation admission/refusal controls; no model or GUI',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names}}, indent=2) + '\n', encoding='utf-8')

target = 't000252'
proposal = parse(json.dumps({
    'kind': 'replace_and_save', 'field_x': 150, 'field_y': 277,
    'save_x': 270, 'save_y': 277, 'text': target,
    'rationale': 'visible field and Save'}), target)
common = dict(expected_text=target, field_target_box=[60, 264, 248, 291],
              save_target_box=[248, 264, 295, 291],
              private_redacted_boxes=[], observation_id='current',
              current_observation_id='current')
allowed = authorize(proposal, **common)
assert allowed['authorized'] is True and len(allowed['steps']) == 5

cases = [
    ('redacted-field', proposal,
     dict(common, private_redacted_boxes=[[60, 264, 248, 291]]),
     'required_input_target_intersects_redaction'),
    ('stale', proposal, dict(common, current_observation_id='new'),
     'observation_identity_mismatch'),
    ('field-outside', dict(proposal, field_x=300), common,
     'field_point_outside_target'),
    ('save-outside', dict(proposal, save_x=400), common,
     'save_point_outside_target'),
    ('wrong-text', dict(proposal, text='wrong'), common,
     'replacement_text_mismatch'),
    ('stop', {'kind': 'stop', 'reason': 'redacted'}, common,
     'planner_requested_stop'),
]
refusals = []
for label, candidate, arguments, reason in cases:
    result = authorize(candidate, **arguments)
    assert result == {'authorized': False, 'reason': reason}
    refusals.append({'case': label, 'reason': reason})

bad = [
    '{}', '{"kind":"stop","reason":""}',
    json.dumps(dict(proposal, text='wrong')),
    json.dumps({key: value for key, value in proposal.items() if key != 'save_y'}),
    json.dumps(dict(proposal, field_x=150.5)),
]
schema_refusals = []
for index, text in enumerate(bad):
    try:
        parse(text, target)
    except ValueError as exc:
        schema_refusals.append({'index': index, 'error': str(exc)})
    else:
        raise AssertionError('invalid mutation proposal accepted')

result = {'allowed_unredacted_mutations': 1, 'gate_refusals': len(refusals),
          'schema_refusals': len(schema_refusals), 'model_calls': 0,
          'gui_actions': 0}
(R / 'refusals.json').write_text(json.dumps(refusals + schema_refusals, indent=2) + '\n', encoding='utf-8')
(R / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
