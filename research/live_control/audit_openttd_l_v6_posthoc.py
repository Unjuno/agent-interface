"""Audit retained v6 artifacts after the preregistered turn-limit path exposed a harness defect."""
import hashlib
import json
from pathlib import Path

from semantic_checkpoint_v4 import next_checkpoint_turn, parse
from timing_envelope_v1 import interval, validate

HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-06'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prereg = read(BASE / 'preregistration.json')
    assert prereg['status'] == 'PREREGISTERED_BEFORE_EXECUTION'
    for name, digest in prereg['sources'].items():
        path = HERE.parent / name if name.startswith('openttd_task/') else HERE / name
        assert sha(path) == digest, name

    negative = read(BASE / 'negative-control-supervisor/result.json')
    assert negative['success'] and negative['failure_outcome']['journal_calls'] == 2
    root = BASE / 'fixed-astra'
    control = BASE / 'fixed-astra-control'
    error = read(control / 'error.json')
    assert error == {'type': 'RuntimeError', 'detail': 'driver exited before failure-evaluation.json', 'automatic_retry': False}
    assert 'proposal limit; no implicit finish success' in (control / 'driver-stderr.txt').read_text(encoding='utf-8')
    assert (root / 'abort.json').exists()
    assert not (root / 'finish.json').exists()
    assert not (root / 'failure-evaluation.json').exists()
    assert not (root / 'result.json').exists()

    calls = read(root / 'calls.json')
    assert len(calls) == 50
    assert [call['result']['request']['command']['op'] for call in calls[:2]] == ['clock', 'submit']
    assert calls[1]['result']['request']['command']['steps'] == [
        {'op': 'chord', 'modifier': 'Control_L', 'key': '2'}, {'op': 'observe'}]
    turns = read(control / 'turns.json')
    assert len(turns) == 12 and all(row['kind'] == 'act' for row in turns)
    required = None
    models = []
    for row in turns:
        turn = row['turn']
        records = [json.loads(line) for line in (root / f'model-{turn}' / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
        message = next(e['item']['text'] for e in records if e.get('type') == 'item.completed')
        typed = parse(message, required, 'transparent')
        assert typed == read(root / f'typed-{turn}.json')
        assert read(root / f'proposal-{turn}.json')['steps'] == typed['steps']
        usage = next(e['usage'] for e in records if e.get('type') == 'turn.completed')
        models.append({'turn': turn, 'kind': typed['kind'], 'usage': usage})
        new_required = next_checkpoint_turn(turn, typed)
        if new_required is not None:
            required = new_required
        elif required is not None and typed['checkpoint']['status'] == 'observed':
            required = None
    for index in range(12):
        group = calls[2 + index * 4:2 + (index + 1) * 4]
        assert [call['result']['request']['command']['op'] for call in group] == ['clock', 'submit', 'clock', 'submit']
        assert group[1]['result']['request']['command']['steps'] == [{'op': 'observe'}]
        assert group[3]['result']['request']['command']['steps'] == read(root / f'typed-{index + 1}.json')['steps'] + [{'op': 'observe'}]

    timing = [validate(json.loads(line)) for line in (control / 'timing-envelope.jsonl').read_text().splitlines()]
    model_wait = []
    feedback = []
    for row in turns:
        turn = row['turn']
        begin = next(e for e in timing if e['event'] == 'planner_request_started' and e['details'].get('turn') == turn)
        end = next(e for e in timing if e['event'] == 'planner_proposal_received' and e['details'].get('turn') == turn)
        model_wait.append(interval(begin, end))
        published = next(e for e in timing if e['event'] == 'proposal_published' and e['details'].get('turn') == turn)
        useful = next(e for e in timing if e['event'] == 'first_useful_feedback_detected' and e['details'].get('turn') == turn)
        feedback.append(interval(published, useful))

    events = [json.loads(line) for line in (root / 'runtime/events.jsonl').read_text().splitlines()]
    observations = [e for e in events if e.get('event') == 'observation']
    terminals = [e for e in events if e.get('event') == 'terminal']
    assert len(observations) == 52
    assert terminals and all(e['release']['verified'] and not e['release']['keys_down'] and not e['release']['buttons_down'] for e in terminals)
    preaction = read(root / 'preaction.json')
    report = {
        'artifact_audit_passed': True,
        'preregistered': True,
        'hard_success': False,
        'independent_task_outcome': 'unavailable',
        'outcome_limit': 'the driver raised at its proposal-loop else branch before consuming the supervisor abort, so no independent finish evaluation was emitted',
        'harness_failure': error,
        'negative_control': {'passed': True, 'model_calls': 0, 'durable_calls': 2, 'pointer_steps': 0},
        'preaction_duration_ms': preaction['duration_ns'] / 1e6,
        'model_turns': models,
        'model_wait_total_ms': sum(v['duration_ns'] for v in model_wait) / 1e6,
        'proposal_to_useful_feedback_total_ms': sum(v['duration_ns'] for v in feedback) / 1e6,
        'input_tokens_total': sum(v['usage']['input_tokens'] for v in models),
        'cached_input_tokens_total': sum(v['usage']['cached_input_tokens'] for v in models),
        'runtime_exact_frames': len(observations),
        'durable_calls': len(calls),
        'checkpoint_pending_at_terminal': required,
        'last_frame_sha256': sha(root / 'runtime' / '052.png'),
        'automatic_retry': False,
        'interpretation': 'the general sign-to-tile instruction did not produce a model verify or safe stop within 12 turns; it increased deliberation versus v5, while task correctness is unscored because of the retained harness failure',
        'scope': 'one candidate episode; no correctness, latency-distribution, human-tempo, or general token claim',
        'audit_sha256': sha(Path(__file__)),
    }
    (BASE / 'posthoc-audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
