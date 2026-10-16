"""Offline controls for policy-bound mutation admission."""
import hashlib
import json
from pathlib import Path

from policy_bound_mutation_gate_v1 import authorize
from policy_bound_mutation_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/policy-bound-mutation-controls-01'
R.mkdir(exist_ok=False)
names = ['probe_policy_bound_mutation_gate_v1.py',
         'policy_bound_mutation_gate_v1.py', 'policy_bound_mutation_schema_v1.py',
         'redaction_mutation_gate_v1.py', 'redaction_action_gate_v1.py']
(R / 'plan.json').write_text(json.dumps({
    'scope': 'offline policy/observation binding controls; no model or GUI',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names}}, indent=2) + '\n', encoding='utf-8')

presented = {'observation_id': 'obs-1', 'policy_id': 'full-control',
             'policy_version': 1}
proposal = parse(json.dumps({
    'kind': 'replace_and_save', **presented,
    'field_x': 150, 'field_y': 277, 'save_x': 270, 'save_y': 277,
    'text': 't000253', 'rationale': 'visible targets'}),
    expected_text='t000253', presented_binding=presented)
common = dict(expected_text='t000253', field_target_box=[60, 264, 248, 291],
              save_target_box=[248, 264, 295, 291], private_redacted_boxes=[],
              presented_binding=presented, current_binding=presented)
assert authorize(proposal, **common)['authorized'] is True

cases = [
    ('policy-id', dict(common, current_binding=dict(presented, policy_id='hide-field')),
     'policy_binding_mismatch'),
    ('policy-version', dict(common, current_binding=dict(presented, policy_version=2)),
     'policy_binding_mismatch'),
    ('observation', dict(common, current_binding=dict(presented, observation_id='obs-2')),
     'observation_identity_mismatch'),
    ('redacted-target', dict(common, private_redacted_boxes=[[60, 264, 248, 291]]),
     'required_input_target_intersects_redaction'),
]
refusals = []
for label, arguments, reason in cases:
    result = authorize(proposal, **arguments)
    assert result == {'authorized': False, 'reason': reason}
    refusals.append({'case': label, 'reason': reason})
tampered = dict(proposal, policy_id='other')
assert authorize(tampered, **common) == {
    'authorized': False, 'reason': 'proposal_binding_mismatch'}
refusals.append({'case': 'proposal-binding', 'reason': 'proposal_binding_mismatch'})

bad = [
    '{}', json.dumps({key: value for key, value in proposal.items()
                      if key != 'policy_version'}),
    json.dumps(dict(proposal, policy_version='1')),
    json.dumps(dict(proposal, policy_id='other')),
    json.dumps(dict(proposal, text='wrong')),
]
schema_refusals = []
for index, text in enumerate(bad):
    try:
        parse(text, expected_text='t000253', presented_binding=presented)
    except ValueError as exc:
        schema_refusals.append({'index': index, 'error': str(exc)})
    else:
        raise AssertionError('invalid bound proposal accepted')

result = {'allowed_stable_policy': 1, 'gate_refusals': len(refusals),
          'schema_refusals': len(schema_refusals), 'model_calls': 0,
          'gui_actions': 0}
(R / 'refusals.json').write_text(json.dumps(refusals + schema_refusals, indent=2) + '\n', encoding='utf-8')
(R / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
