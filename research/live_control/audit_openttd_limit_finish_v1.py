"""Cross-platform audit for the model-free bounded-limit finish probe."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-limit-01'
ROOT = BASE / 'fixed-astra'
CONTROL = BASE / 'probe-control'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


plan = read(CONTROL / 'plan.json')
assert plan['status'] == 'FROZEN_BEFORE_EXECUTION'
for name, digest in plan['sources'].items():
    assert sha(HERE / name) == digest, name
result = read(CONTROL / 'result.json')
failure = read(ROOT / 'failure-evaluation.json')
assert result['success'] and result['model_calls'] == 0 and result['pointer_steps'] == 0
assert result['observe_only_proposals'] == 12 and result['durable_calls'] == 50
assert failure['failure_mode'] == 'bounded_turn_limit' and failure['proposals_executed'] == 12
assert failure['journal_calls'] == 50 and failure['evaluation']['success'] is False
assert failure['evaluation']['changed_surrounding_tiles'] == []
assert read(ROOT / 'runtime/evaluation.json')['success'] is False
events = [json.loads(line) for line in (ROOT / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
pointer = [event for event in events if str(event.get('operation', '')).startswith('pointer_')]
assert pointer == []
terminals = [event for event in events if event.get('event') == 'terminal']
assert terminals and all(event['release']['verified'] and not event['release']['keys_down'] and
                         not event['release']['buttons_down'] for event in terminals)
calls = read(ROOT / 'calls.json')
assert len(calls) == 50
assert [call['result']['request']['command']['op'] for call in calls[:2]] == ['clock', 'submit']
for index in range(12):
    group = calls[2 + index * 4:2 + (index + 1) * 4]
    assert [call['result']['request']['command']['op'] for call in group] == ['clock', 'submit', 'clock', 'submit']
    assert group[1]['result']['request']['command']['steps'] == [{'op': 'observe'}]
    assert group[3]['result']['request']['command']['steps'] == [{'op': 'observe'}, {'op': 'observe'}]
report = {
    'audit_passed': True,
    'model_calls': 0,
    'pointer_steps': 0,
    'observe_only_proposals': 12,
    'durable_calls': 50,
    'runtime_observations': len([event for event in events if event.get('event') == 'observation']),
    'independent_outcome': 'bounded_turn_limit',
    'driver_exit_code': result['driver_exit_code'],
    'supervisor_wall_ms': result['supervisor_wall_ms'],
    'audit_sha256': sha(Path(__file__)),
}
(BASE / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
