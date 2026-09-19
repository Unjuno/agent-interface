"""Offline compatibility and rejection controls for planner evidence v4."""
import copy
import hashlib
import json
from pathlib import Path

from planner_evidence_v4 import present


H = Path(__file__).resolve().parent
R = H / 'results/planner-evidence-controls-04'
R.mkdir(exist_ok=False)


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = ['probe_planner_evidence_v4.py', 'planner_evidence_v4.py',
         'planner_evidence_v2.py', 'checkpoint_contract_v1.py']
dump('plan.json', {
    'scope': 'offline durable revision compatibility and refusal; no model or GUI calls',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})

archived = json.loads((H / 'results/partial-terminal-live-01/before-return/decision-state.json').read_text(encoding='utf-8'))
valid = []
for revision in ('durable-submit-v4', 'durable-submit-v5', 'durable-submit-v6'):
    phase = copy.deepcopy(archived['phase'])
    phase['exchanges'][0]['state']['format'] = revision
    view = present(
        archived['unknown'], expected_request_id=archived['unknown']['request_id'],
        expected_contract=archived['strict']['binding']['expected_contract'],
        phase_report=phase, prior_steps=archived['steps'])
    assert view['execution']['programs'][0]['journal_format'] == revision
    assert view['execution']['programs'][0]['terminal'] == 'expired'
    valid.append({'revision': revision, 'view': view})

refusals = []
for revision in ('durable-submit-v3', 'durable-submit-v7', None):
    phase = copy.deepcopy(archived['phase'])
    phase['exchanges'][0]['state']['format'] = revision
    try:
        present(
            archived['unknown'], expected_request_id=archived['unknown']['request_id'],
            expected_contract=archived['strict']['binding']['expected_contract'],
            phase_report=phase, prior_steps=archived['steps'])
    except ValueError as exc:
        refusals.append({'case': f'journal-{revision}', 'error': str(exc)})
    else:
        raise AssertionError('unknown journal revision accepted')

for key, value in (
        ('expected_request_id', 'wrong-request'),
        ('expected_contract', {'kind': 'saved_form_value', 'expected': 'wrong'})):
    kwargs = {
        'expected_request_id': archived['unknown']['request_id'],
        'expected_contract': archived['strict']['binding']['expected_contract'],
        'phase_report': archived['phase'], 'prior_steps': archived['steps'],
    }
    kwargs[key] = value
    try:
        present(archived['unknown'], **kwargs)
    except ValueError as exc:
        refusals.append({'case': key, 'error': str(exc)})
    else:
        raise AssertionError('binding conflict accepted')

dump('valid.json', valid)
dump('refusals.json', refusals)
result = {'valid_revisions': 3, 'refusals': 5, 'model_calls': 0, 'gui_actions': 0}
dump('result.json', result)
print(json.dumps(result, indent=2))
