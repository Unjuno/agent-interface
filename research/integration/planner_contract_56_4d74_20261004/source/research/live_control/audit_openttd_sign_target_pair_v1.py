"""Audit and score the fixed-image opaque/transparent sign targeting ABBA."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-sign-target-pair-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan = read(ROOT / 'preregistration.json')
assert plan['status'] == 'PREREGISTERED_BEFORE_MODEL_CALLS'
assert plan['order'] == ['opaque-sign-background', 'transparent-sign-background',
                         'transparent-sign-background', 'opaque-sign-background']
for name, digest in plan['sources'].items():
    assert sha(HERE / name) == digest, name
assert sha(ROOT / 'prompt.txt') == plan['same_prompt_sha256']
expected = plan['hidden_scoring_reference']
rows = []
for index, condition in enumerate(plan['order'], 1):
    root = ROOT / f'call-{index}-{condition}'
    runner_plan = read(root / 'plan.json')
    process = read(root / 'process.json')
    assert process['exit_code'] == 0
    assert runner_plan['requested_model'] == plan['model'] and runner_plan['requested_effort'] == plan['effort']
    assert runner_plan['image_sha256'] == plan['conditions'][condition]['sha256']
    assert sha(root / 'prompt.txt') == plan['same_prompt_sha256']
    records = [json.loads(line) for line in (root / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
    messages = [event['item']['text'] for event in records if event.get('type') == 'item.completed']
    assert len(messages) == 1
    try:
        proposal = json.loads(messages[0])
        assert set(proposal) == {'start_x', 'start_y', 'end_x', 'end_y'}
        assert all(type(value) is int for value in proposal.values())
        parse_error = None
    except (json.JSONDecodeError, AssertionError) as error:
        proposal = None
        parse_error = type(error).__name__ + ': ' + str(error)
    usage = next(event['usage'] for event in records if event.get('type') == 'turn.completed')
    passed = proposal is not None and abs(proposal['start_x'] - expected['start'][0]) <= 12 and abs(proposal['start_y'] - expected['start'][1]) <= 6 and abs(proposal['end_x'] - expected['end'][0]) <= 12 and abs(proposal['end_y'] - expected['end'][1]) <= 6
    rows.append({'call': index, 'condition': condition, 'proposal': proposal,
                 'parse_error': parse_error, 'endpoint_gate_passed': passed,
                 'runner_wall_ms': (process['exited_ns'] - process['started_ns']) / 1e6,
                 'usage': usage, 'raw_message_sha256': hashlib.sha256(messages[0].encode()).hexdigest()})
summary = {}
for condition in plan['conditions']:
    selected = [row for row in rows if row['condition'] == condition]
    summary[condition] = {
        'passes': sum(row['endpoint_gate_passed'] for row in selected),
        'calls': len(selected),
        'input_tokens': sum(row['usage']['input_tokens'] for row in selected),
        'cached_input_tokens': sum(row['usage']['cached_input_tokens'] for row in selected),
        'runner_wall_ms': sum(row['runner_wall_ms'] for row in selected),
    }
report = {
    'audit_passed': True,
    'preregistered': True,
    'rows': rows,
    'summary': summary,
    'decision': 'descriptive fixed-image result only; require fresh live execution and more geometries before promotion',
    'scope': plan['scope'],
    'audit_sha256': sha(Path(__file__)),
}
(ROOT / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
