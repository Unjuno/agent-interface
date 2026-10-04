"""Reject append, partial selection and caller-supplied steps under overwrite authority."""
import copy
import hashlib
import json
from pathlib import Path

from authorized_redacted_mutation_gate_v1 import authorize
from policy_bound_mutation_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/authorized-redacted-plan-controls-01'
R.mkdir(exist_ok=False)
TEXT = 't000254'
FIELD = [60, 264, 248, 291]
SAVE = [248, 264, 295, 291]
BINDING = {'observation_id': 'runtime-sequence-10',
           'policy_id': 'replace-hidden-value', 'policy_version': 3}
BASE = {'kind': 'replace_and_save', **BINDING, 'field_x': 150,
        'field_y': 277, 'save_x': 270, 'save_y': 277, 'text': TEXT,
        'rationale': 'exact whole replacement'}


def refusal(value):
    try:
        parse(json.dumps(value), expected_text=TEXT, presented_binding=BINDING)
    except ValueError as exc:
        return {'accepted': False, 'reason': str(exc)}
    return {'accepted': True}


cases = {}
for name, mutate in (
        ('append_kind', lambda row: row.__setitem__('kind', 'append_and_save')),
        ('insert_kind', lambda row: row.__setitem__('kind', 'insert_and_save')),
        ('caller_steps', lambda row: row.__setitem__('steps', [
            {'op': 'text', 'text': TEXT}])),
        ('selection_range', lambda row: row.update(
            {'selection_start': 0, 'selection_end': 2})),
        ('append_flag', lambda row: row.__setitem__('append', True)),
        ('missing_text', lambda row: row.pop('text')),
        ('different_text', lambda row: row.__setitem__('text', 't000255')),
        ('stop_with_coordinates', lambda row: row.update(
            {'kind': 'stop', 'reason': 'no', 'field_x': 150}))):
    candidate = copy.deepcopy(BASE)
    mutate(candidate)
    cases[name] = refusal(candidate)
assert all(not row['accepted'] for row in cases.values())

proposal = parse(json.dumps(BASE), expected_text=TEXT,
                 presented_binding=BINDING)
authority = {'kind': 'replace_entire_text_and_save', **BINDING,
             'field_target_box': FIELD, 'save_target_box': SAVE,
             'replacement_text_sha256': hashlib.sha256(TEXT.encode()).hexdigest()}
gate = authorize(proposal, expected_text=TEXT, field_target_box=FIELD,
                 save_target_box=SAVE, private_redacted_boxes=[FIELD],
                 presented_binding=BINDING, current_binding=BINDING,
                 mutation_authority=authority)
assert gate['authorized']
assert gate['steps'] == [
    {'op': 'pointer_click', 'x': 150, 'y': 277, 'duration_ms': 80},
    {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'},
    {'op': 'text', 'text': TEXT},
    {'op': 'pointer_click', 'x': 270, 'y': 277, 'duration_ms': 80},
    {'op': 'observe'},
]
plan = {'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                    for name in ('policy_bound_mutation_schema_v1.py',
                                 'authorized_redacted_mutation_gate_v1.py',
                                 'probe_authorized_redacted_plan_shape_v1.py')}}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(R / 'refusals.json').write_text(json.dumps(cases, indent=2) + '\n')
(R / 'allowed-steps.json').write_text(json.dumps(gate, indent=2) + '\n')
result = {'whole_replacement_plan': 1, 'shape_refusals': len(cases),
          'model_calls': 0, 'gui_actions': 0}
(R / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
