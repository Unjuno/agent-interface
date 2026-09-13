"""Audit the fresh successful adaptive OpenTTD TimingEnvelope episode."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
from append_checkpoint_v1 import load, inspect
from received_continuation_v1 import start, advance
from openttd_proposal_schema_v5 import parse
from timing_envelope_v1 import interval, validate

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'observation_tiles'))
from tile_transport import Decoder


def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def sha_bytes(value): return hashlib.sha256(value).hexdigest()


def source_with_hash(path, digest):
    if path.exists() and sha(path) == digest:
        return path
    archived = HERE / 'frozen_sources' / digest / path.name
    assert archived.exists() and sha(archived) == digest, str(path)
    return archived


def main():
    root = HERE / 'results/timing-envelope-openttd-08'
    control = HERE / 'results/timing-envelope-openttd-control-08'
    runtime = root / 'runtime'
    for directory in (root, control):
        for name, digest in read(directory / 'plan.json')['sources'].items():
            source_with_hash(HERE / name, digest)
    for name, digest in read(runtime / 'manifest.json')['sources'].items():
        source_with_hash(HERE.parent / name, digest)

    endpoint = read(root / 'endpoint.json')
    events = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    state = start(endpoint['socket'])
    calls = read(root / 'calls.json')
    assert len(calls) == 28

    def replay(exchange):
        nonlocal state
        request, reply = exchange['request'], exchange['reply']
        assert request['after'] == state['cursor']
        assert reply['records'] == events[request['after']:reply['cursor']]
        state = advance(state, endpoint['socket'], request['after'], reply)
        expected = exchange['state']['continuation'] if 'state' in exchange else exchange['continuation']
        assert state == expected

    initial = read(root / 'initial.json')
    replay(initial)
    for call in calls:
        replay(call['result'])
        assert call['result']['state']['pending'] is None
    assert load(root / 'journal.jsonl') == calls[-1]['result']['state']
    assert inspect(root / 'journal.jsonl')[1] == 57
    replay(read(root / 'finish.json'))

    handoffs = read(control / 'turns.json')
    assert len(handoffs) == 8
    models = []
    candidate_images = list(root.glob('*.png')) + list(runtime.glob('*.png'))
    for turn in range(1, 9):
        directory = root / f'model-{turn}'
        plan = read(directory / 'plan.json')
        expected_route = ('gpt-5.6-luna', 'low') if turn <= 2 else ('gpt-6-astra', 'medium')
        assert (plan['requested_model'], plan['requested_effort']) == expected_route
        assert plan['runner_sha256'] == sha(HERE / 'model_pair_runner_v2.py')
        assert sum(sha(image) == plan['image_sha256'] for image in candidate_images) == 1
        assert (directory / 'prompt.txt').read_text() == (root / f'prompt-{turn}.txt').read_text()
        process = read(directory / 'process.json')
        assert process['exit_code'] == 0
        lines = (directory / 'events.jsonl').read_bytes().splitlines(keepends=True)
        arrivals = [json.loads(line) for line in (directory / 'arrivals.jsonl').read_text().splitlines()]
        assert len(lines) == len(arrivals)
        for line, arrival in zip(lines, arrivals):
            assert sha_bytes(line) == arrival['sha256'] and len(line) == arrival['bytes']
        records = [json.loads(line) for line in lines]
        items = [event['item'] for event in records if event.get('type') == 'item.completed']
        assert len(items) == 1 and items[0]['type'] == 'agent_message'
        typed = parse(items[0]['text'])
        assert typed == read(root / f'typed-{turn}.json')
        usage = next(event['usage'] for event in records if event.get('type') == 'turn.completed')
        models.append({'turn': turn, 'model': expected_route[0], 'effort': expected_route[1],
                       'kind': typed['kind'], 'usage': usage,
                       'runner_wall_ms': (process['exited_ns'] - process['started_ns']) / 1e6})
        if turn <= 7:
            proposal = read(root / f'proposal-{turn}.json')
            assert proposal == {'steps': typed['steps'], 'rationale': typed['rationale']}
            applied = read(root / f'applied-{turn}.json')
            group = calls[(turn - 1) * 4:turn * 4]
            assert [call['result']['request']['command']['op'] for call in group] == ['clock', 'submit', 'clock', 'submit']
            assert group[1]['result']['request']['command']['steps'] == [{'op': 'observe'}]
            assert group[3]['result']['request']['command']['steps'] == typed['steps'] + [{'op': 'observe'}]
            assert group[3]['result'] == applied['result']
        else:
            assert typed == read(root / 'visual-verdict.json') and typed['kind'] == 'verify'

    observations = [event for event in events if event.get('event') == 'observation']
    assert len(observations) == 44
    decoder = Decoder('live-control')
    for number, event in enumerate(observations, 1):
        decoded = decoder.accept((runtime / f'{number:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as image:
            assert (image.width, image.height, image.mode, image.tobytes()) == (decoded.width, decoded.height, decoded.mode, decoded.pixels)
    terminals = [event for event in events if event.get('event') == 'terminal']
    assert terminals and all(event['release']['verified'] is True and event['release']['keys_down'] == [] and event['release']['buttons_down'] == [] for event in terminals)
    evaluation = next(event for event in events if event.get('event') == 'independent_evaluation')
    assert evaluation['success'] is True and all(evaluation['checks'].values())
    assert evaluation['changed_surrounding_tiles'] == []
    result = read(control / 'result.json')
    assert result['success'] is True and read(root / 'result.json')['exit_code'] == 0

    timing = [validate(json.loads(line)) for line in (control / 'timing-envelope.jsonl').read_text().splitlines()]
    assert [event['sequence'] for event in timing] == list(range(1, 53))
    observed = [event for event in timing if event['state'] == 'OBSERVED']
    assert len({event['clock']['domain_id'] for event in observed}) == 1
    missing = [event for event in timing if event['state'] == 'NOT_RECORDED']
    assert {event['event'] for event in missing} == {'runtime_receipt', 'os_injection', 'provider_request_received', 'provider_first_token'}

    def per_turn(event, turn):
        return next(row for row in timing if row['event'] == event and row['details'].get('turn') == turn)
    model_intervals = [interval(per_turn('planner_request_started', turn), per_turn('planner_proposal_received', turn)) for turn in range(1, 9)]
    feedback_intervals = [interval(per_turn('proposal_published', turn), per_turn('first_useful_feedback_detected', turn)) for turn in range(1, 8)]
    assert all(row['status'] == 'comparable' for row in model_intervals + feedback_intervals)
    first = next(row for row in timing if row['event'] == 'initial_observation_detected')
    final = next(row for row in timing if row['event'] == 'semantic_completion_detected')
    whole = interval(first, final)
    assert whole == result['initial_observation_to_semantic_completion']
    assert not (control / 'error.json').exists() and not (root / 'abort.json').exists()
    assert not Path(endpoint['socket']).exists() and not Path(endpoint['cancel_socket']).exists()

    report = {
        'audit_passed': True,
        'model_turns': models,
        'model_wait_total_ms': sum(row['duration_ns'] for row in model_intervals) / 1e6,
        'proposal_to_useful_feedback_ms': [row['duration_ns'] / 1e6 for row in feedback_intervals],
        'proposal_to_useful_feedback_total_ms': sum(row['duration_ns'] for row in feedback_intervals) / 1e6,
        'initial_observation_to_semantic_completion_ms': whole['duration_ns'] / 1e6,
        'initial_to_completion_uncertainty_ms': whole['uncertainty_ns'] / 1e6,
        'input_tokens_total': sum(row['usage']['input_tokens'] for row in models),
        'output_tokens_total': sum(row['usage']['output_tokens'] for row in models),
        'reasoning_output_tokens_total': sum(row['usage']['reasoning_output_tokens'] for row in models),
        'runtime_exact_frames': len(observations),
        'contact_sheets': len(list(root.glob('planner-*.png'))),
        'durable_calls': len(calls),
        'append_records': inspect(root / 'journal.jsonl')[1],
        'missing_endpoints': sorted(row['event'] for row in missing),
        'independent_checks': evaluation['checks'],
        'scope': 'one fresh successful adaptive-model OpenTTD episode; prior failures retained; no matched baseline, causal speedup or human-tempo claim',
        'audit_sha256': sha(Path(__file__)),
    }
    (root / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
