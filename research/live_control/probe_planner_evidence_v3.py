"""Adversarial caller-binding controls for strict compact planner evidence."""
import copy
import hashlib
import json
import os
from pathlib import Path
import planner_evidence_v2 as prior
import planner_evidence_v3 as candidate

H = Path(__file__).resolve().parent
R = Path(os.environ.get('PLANNER_EVIDENCE_V3_OUT', H / 'results/planner-evidence-controls-03'))
R.mkdir(exist_ok=False)
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

form = H / 'results/checkpoint-recovery-form-01'
calc = H / 'results/checkpoint-decision-calc-01'
losses = read(form / 'losses.json')
turns = read(calc / 'turns.json')
specs = [
    ('form_unknown', losses[0]['recovered']['state']['last_resolution'], None, None, True),
    ('form_verified', losses[1]['recovered']['state']['last_resolution'], None, None, True),
    ('calc_unknown_partial', turns[1]['feedback']['checkpoint_resolution'],
     turns[0]['phases'], turns[0]['proposal']['steps'], False),
    ('calc_verified', turns[1]['checkpoint']['state']['last_resolution'], None, None, False),
]

valid = []
for name, resolution, phase, steps, recovered in specs:
    expected_id = resolution['request_id']
    expected_contract = resolution['checkpoint']['evidence']['contract']
    old = prior.present(resolution, phase_report=phase, prior_steps=steps, recovered=recovered)
    new = candidate.present(resolution, expected_request_id=expected_id,
                            expected_contract=expected_contract, phase_report=phase,
                            prior_steps=steps, recovered=recovered)
    without_binding = copy.deepcopy(new)
    binding = without_binding.pop('binding')
    assert without_binding == old
    assert binding == {'expected_request_id': expected_id,
                       'expected_contract': expected_contract,
                       'match': 'verified_before_presentation'}
    valid.append(name)

base = losses[0]['recovered']['state']['last_resolution']
base_id = base['request_id']
base_contract = base['checkpoint']['evidence']['contract']
controls = []


def refuse(name, function):
    try:
        function()
    except (TypeError, ValueError) as exc:
        controls.append({'name': name, 'error': type(exc).__name__, 'detail': str(exc)})
    else:
        raise AssertionError(name)


refuse('wrong_expected_request_id', lambda: candidate.present(
    base, expected_request_id='unrelated-query', expected_contract=base_contract))
refuse('empty_expected_request_id', lambda: candidate.present(
    base, expected_request_id='', expected_contract=base_contract))
refuse('oversized_expected_request_id', lambda: candidate.present(
    base, expected_request_id='x' * 257, expected_contract=base_contract))
refuse('wrong_expected_form_value', lambda: candidate.present(
    base, expected_request_id=base_id,
    expected_contract={'kind': 'saved_form_value', 'expected': 'different-value'}))
refuse('wrong_expected_contract_kind', lambda: candidate.present(
    base, expected_request_id=base_id,
    expected_contract={'kind': 'saved_cells', 'expected': {'A1': 480}}))
refuse('missing_expected_contract_field', lambda: candidate.present(
    base, expected_request_id=base_id,
    expected_contract={'kind': 'saved_form_value'}))
refuse('unsupported_expected_contract', lambda: candidate.present(
    base, expected_request_id=base_id,
    expected_contract={'kind': 'other', 'expected': 't000240'}))
mutated = copy.deepcopy(base)
mutated['request_id'] = 'other'
refuse('record_and_resolution_identity_disagree', lambda: candidate.present(
    mutated, expected_request_id='other', expected_contract=base_contract))
mutated = copy.deepcopy(base)
mutated['checkpoint']['evidence'].pop('contract')
refuse('record_contract_missing', lambda: candidate.present(
    mutated, expected_request_id=base_id, expected_contract=base_contract))

assert len(controls) == 9
sources = [Path(__file__), H / 'planner_evidence_v3.py',
           H / 'planner_evidence_v2.py', H / 'planner_evidence_v1.py',
           H / 'checkpoint_contract_v1.py', form / 'losses.json', calc / 'turns.json']
report = {
    'scope': 'offline caller-expected identity and completion-contract binding; no model calls or input',
    'valid_prior_views_preserved_except_explicit_binding': valid,
    'adversarial_refusals': controls,
    'model_calls': 0,
    'actions_executed': 0,
    'candidate': 'planner_evidence_v3.py',
    'sources': {str(path.relative_to(H)): sha(path) for path in sources},
}
(R / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
