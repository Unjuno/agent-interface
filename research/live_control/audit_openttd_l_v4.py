"""Audit the preregistered OpenTTD typed-view recovery allocation."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

import audit_openttd_matched_v2 as shared
from append_checkpoint_v1 import inspect, load
from received_continuation_v1 import advance, start
from semantic_checkpoint_v3 import expand_view, next_checkpoint_turn, parse
from timing_envelope_v1 import interval, validate

HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-04'
sys.path.insert(0, str(HERE.parent / 'observation_tiles'))
from tile_transport import Decoder


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prereg = read(BASE / 'preregistration.json')
    assert prereg['status'] == 'PREREGISTERED_BEFORE_EXECUTION'
    assert prereg['execution_order'] == ['negative-control', 'fixed-astra']
    for name, digest in prereg['sources'].items():
        path = HERE.parent / name if name.startswith('openttd_task/') else HERE / name
        shared.source_with_hash(path, digest)

    negative = read(BASE / 'negative-control-supervisor/result.json')
    assert negative['success'] and negative['failure_outcome']['journal_calls'] == 0
    assert negative['failure_outcome']['evaluation']['success'] is False

    root = BASE / 'fixed-astra'
    control = BASE / 'fixed-astra-control'
    runtime = root / 'runtime'
    for directory in (root, control):
        for name, digest in read(directory / 'plan.json')['sources'].items():
            shared.source_with_hash(HERE / name, digest)
    manifest = read(runtime / 'manifest.json')
    assert manifest['save_sha256'] == prereg['task_allocation']['save_sha256']
    for name, digest in manifest['sources'].items():
        shared.source_with_hash(HERE.parent / name, digest)

    events = [json.loads(line) for sorr in [runtime / 'events.jsonl'] for line in sorr.read_text().splitlines()]
    calls = read(root / 'calls.json')
    endpoint = read(root / 'endpoint.json')
    state = start(endpoint['socket'])

    def replay(exchange):
        nonlocal state
        request, reply = exchange['request'], exchange['reply']
        assert request['after'] == state['cursor']
        assert reply['records'] == events[request['after']:reply['cursor']]
        state = advance(state, endpoint['socket'], request['after'], reply)
        expected = exchange['state']['continuation'] if 'state' in exchange else exchange['continuation']
        assert state == expected

    replay(read(root / 'initial.json'))
    for call in calls:
        replay(call['result'])
        assert call['result']['state']['pending'] is None
    assert load(root / 'journal.jsonl') == calls[-1]['result']['state']
    replay(read(root / 'finish.json'))

    turns = read(control / 'turns.json')
    required = None
    models = []
    executed = 0
    view_turns = []
    for row in turns:
        turn = row['turn']
        model = root / f'model-{turn}'
        records = [json.loads(line) for line in (model / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
        message = next(e['item']['text'] for e in records if e.get('type') == 'item.completed')
        typed = parse(message, required)
        assert typed == read(root / f'typed-{turn}.json') and typed['kind'] == row['kind']
        usage = next(e['usage'] for e in records if e.get('type') == 'turn.completed')
        models.append({'turn': turn, 'kind': typed['kind'], 'usage': usage})
        applied_path = root / f'applied-{turn}.json'
        if typed['kind'] in {'act', 'view'}:
            assert applied_path.exists()
            expected_steps = expand_view(typed) if typed['kind'] == 'view' else typed['steps']
            proposal = read(root / f'proposal-{turn}.json')
            assert proposal['typed_kind'] == typed['kind'] and proposal['steps'] == expected_steps
            group = calls[executed * 4:(executed + 1) * 4]
            assert [c['result']['request']['command']['op'] for c in group] == ['clock', 'submit', 'clock', 'submit']
            assert group[1]['result']['request']['command']['steps'] == [{'op': 'observe'}]
            assert group[3]['result']['request']['command']['steps'] == expected_steps + [{'op': 'observe'}]
            executed += 1
            if typed['kind'] == 'view':
                view_turns.append(turn)
                assert required is not None and typed['checkpoint']['status'] == 'uncertain'
            else:
                new = next_checkpoint_turn(turn, typed)
                if new is not None:
                    required = new
                elif required is not None and typed['checkpoint']['status'] == 'observed':
                    required = None
        else:
            assert not applied_path.exists()
    assert len(calls) == executed * 4

    observations = [e for e in events if e.get('event') == 'observation']
    artifacts = sorted(runtime.glob('*.ait'))
    assert len(artifacts) == len(observations)
    decoder = Decoder('live-control')
    for artifact, event in zip(artifacts, observations):
        decoded = decoder.accept(artifact.read_bytes())
        with Image.open(runtime / Path(event['image']).name) as image:
            assert (image.width, image.height, image.mode, image.tobytes()) == (decoded.width, decoded.height, decoded.mode, decoded.pixels)
    terminals = [e for e in events if e.get('event') == 'terminal']
    assert terminals and all(e['release']['verified'] and not e['release']['keys_down'] and not e['release']['buttons_down'] for e in terminals)
    chord_steps = [e for e in events if e.get('event') == 'step_started' and e.get('operation') == 'chord']
    assert len(chord_steps) == len(view_turns)

    evaluation = read(runtime / 'evaluation.json')
    success = evaluation['success'] is True
    if success:
        result = read(control / 'result.json')
        assert result['success'] is True and not (root / 'failure-evaluation.json').exists()
    else:
        failure = read(root / 'failure-evaluation.json')
        assert failure['success'] is False and not (root / 'result.json').exists()
        result = read(control / 'error.json')

    timing = [validate(json.loads(line)) for line in (control / 'timing-envelope.jsonl').read_text().splitlines()]
    assert [e['sequence'] for e in timing] == list(range(1, len(timing) + 1))
    model_intervals = []
    feedback = []
    for row in turns:
        turn = row['turn']
        begin = next(e for e in timing if e['event'] == 'planner_request_started' and e['details'].get('turn') == turn)
        end = next(e for e in timing if e['event'] == 'planner_proposal_received' and e['details'].get('turn') == turn)
        model_intervals.append(interval(begin, end))
        if row['kind'] in {'act', 'view'}:
            published = next(e for e in timing if e['event'] == 'proposal_published' and e['details'].get('turn') == turn)
            useful = next(e for e in timing if e['event'] == 'first_useful_feedback_detected' and e['details'].get('turn') == turn)
            feedback.append(interval(published, useful))
    report = {
        'audit_passed': True,
        'preregistered': True,
        'hard_success': success,
        'negative_control': {'passed': True, 'model_calls': 0, 'durable_calls': 0},
        'model_turns': models,
        'model_wait_total_ms': sum(v['duration_ns'] for v in model_intervals) / 1e6,
        'proposal_to_useful_feedback_total_ms': sum(v['duration_ns'] for v in feedback) / 1e6,
        'input_tokens_total': sum(v['usage']['input_tokens'] for v in models),
        'cached_input_tokens_total': sum(v['usage']['cached_input_tokens'] for v in models),
        'runtime_exact_frames': len(observations),
        'contact_sheets': len(list(root.glob('planner-*.png'))),
        'durable_calls': len(calls),
        'append_records': inspect(root / 'journal.jsonl')[1],
        'typed_view_turns': view_turns,
        'typed_view_calls': len(view_turns),
        'checkpoint_pending_at_terminal': required,
        'independent_checks': evaluation['checks'],
        'changed_surrounding_tiles': evaluation['changed_surrounding_tiles'],
        'semantic_completion_ms': result.get('initial_observation_to_semantic_completion', {}).get('duration_ns') / 1e6 if success else None,
        'scope': 'one fresh candidate episode; descriptive comparison only; no broad correctness, latency distribution, human-tempo or token-reduction claim',
        'audit_sha256': sha(Path(__file__)),
    }
    (BASE / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
