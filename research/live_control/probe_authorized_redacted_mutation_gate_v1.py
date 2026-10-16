"""Offline controls for scoped whole-value replacement under redaction."""
import copy
import hashlib
import json
from pathlib import Path

from authorized_redacted_mutation_gate_v1 import authorize
from policy_bound_mutation_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/authorized-redacted-mutation-controls-01'
R.mkdir(exist_ok=False)
FIELD = [60, 264, 248, 291]
SAVE = [248, 264, 295, 291]
TEXT = 't000254'
BINDING = {'observation_id': 'runtime-sequence-10',
           'policy_id': 'replace-hidden-value', 'policy_version': 3}
PROPOSAL = {'kind': 'replace_and_save', **BINDING, 'field_x': 150,
            'field_y': 277, 'save_x': 271, 'save_y': 277, 'text': TEXT,
            'rationale': 'replace the entire authorized field and save'}
AUTHORITY = {'kind': 'replace_entire_text_and_save', **BINDING,
             'field_target_box': FIELD, 'save_target_box': SAVE,
             'replacement_text_sha256': hashlib.sha256(TEXT.encode()).hexdigest()}


def gate(proposal=PROPOSAL, presented=BINDING, current=BINDING,
         authority=AUTHORITY):
    return authorize(proposal, expected_text=TEXT, field_target_box=FIELD,
                     save_target_box=SAVE, private_redacted_boxes=[FIELD],
                     presented_binding=presented, current_binding=current,
                     mutation_authority=authority)


parsed = parse(json.dumps(PROPOSAL), expected_text=TEXT,
               presented_binding=BINDING)
allowed = gate(parsed)
assert allowed['authorized'] and allowed['reason'] == 'authorized_redacted_full_replacement'

cases = {}
cases['missing_authority'] = gate(authority=None)
for name, key, value in (
        ('wrong_kind', 'kind', 'append_text_and_save'),
        ('wrong_observation', 'observation_id', 'runtime-sequence-9'),
        ('wrong_policy', 'policy_id', 'hide-current-text-entry'),
        ('wrong_version', 'policy_version', 2),
        ('wrong_text_hash', 'replacement_text_sha256', '0' * 64),
        ('wrong_field_box', 'field_target_box', [61, 264, 248, 291]),
        ('wrong_save_box', 'save_target_box', [249, 264, 295, 291])):
    changed = copy.deepcopy(AUTHORITY)
    changed[key] = value
    cases[name] = gate(authority=changed)
stale = copy.deepcopy(PROPOSAL)
stale.update({'observation_id': 'runtime-sequence-9',
              'policy_id': 'hide-current-text-entry', 'policy_version': 2})
cases['stale_proposal'] = gate(stale)
outside = copy.deepcopy(PROPOSAL)
outside['field_x'] = 59
cases['outside_field'] = gate(outside)
save_hidden = copy.deepcopy(PROPOSAL)
save_hidden['save_x'] = 247
cases['save_outside'] = gate(save_hidden)
assert all(not result['authorized'] for result in cases.values())
assert cases['stale_proposal']['reason'] == 'proposal_binding_mismatch'
assert all(result['reason'] == 'mutation_authority_mismatch'
           for name, result in cases.items() if name not in
           ('stale_proposal', 'outside_field', 'save_outside'))
assert cases['outside_field']['reason'] == 'field_point_outside_target'
assert cases['save_outside']['reason'] == 'save_point_outside_target'

plan = {'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                    for name in ('authorized_redacted_mutation_gate_v1.py',
                                 'policy_bound_mutation_schema_v1.py',
                                 'probe_authorized_redacted_mutation_gate_v1.py')}}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(R / 'refusals.json').write_text(json.dumps(cases, indent=2) + '\n')
result = {'allowed': 1, 'refused': len(cases), 'model_calls': 0,
          'gui_actions': 0}
(R / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
