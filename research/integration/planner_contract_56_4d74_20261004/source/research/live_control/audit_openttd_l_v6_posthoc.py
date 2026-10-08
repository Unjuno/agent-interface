"""Audit retained v6 artifacts after the preregistered turn-limit path exposed a harness defect."""
import hashlib
import json
from pathlib import Path
import sys

from semantic_checkpoint_v4 import next_checkpoint_turn, parse
from timing_envelope_v1 import interval, validate

HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-06'
sys.path.insert(0, str(HERE.parent / 'openttd_task'))
from guarded_l_score_v1 import score  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observer_records(path):
    records = []
    for line in path.read_text(encoding='utf-8').splitlines():
        marker = line.find('AIT ')
        if marker >= 0:
            records.append(json.loads(line[marker + 4:]))
    return records


def observer_signature(record):
    return tuple((tile['id'], tile['road'], tile['owner']) for tile in record['guard'])


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

    observer_path = root / 'runtime/game-stderr.txt'
    observer = observer_records(observer_path)
    assert len(observer) == 263
    transitions = [index for index in range(1, len(observer))
                   if observer_signature(observer[index]) != observer_signature(observer[index - 1])]
    assert transitions == [91]
    baseline, final = observer[0], observer[-1]
    final_score = score(final, baseline)
    assert not final_score['success']
    assert final_score['checks'] == {
        'target_owned_roads': False,
        'ordered_bidirectional_connections': False,
        'forbidden_tiles_clear': True,
        'surrounding_road_owner_unchanged': True,
    }
    final_tiles = {tile['id']: tile for tile in final['tiles']}
    assert all(final_tiles[tile] == {'id': tile, 'road': True, 'owner': 0}
               for tile in (977, 978, 979))
    assert all(final_tiles[tile] == {'id': tile, 'road': False, 'owner': -1}
               for tile in (1043, 1107, 1041, 1042, 1105, 1106))
    assert final['edges'] == [
        [977, 978, True, True], [978, 979, True, True],
        [979, 1043, False, False], [1043, 1107, False, False],
    ]
    assert all(observer_signature(row) == observer_signature(final) for row in observer[91:])

    drag_turns = []
    for turn in range(1, 13):
        typed = read(root / f'typed-{turn}.json')
        for step in typed['steps']:
            if step['op'] == 'pointer_drag':
                drag_turns.append({'turn': turn, 'points': step['points'],
                                   'duration_ms': step['duration_ms']})
    expected_points = [{'x': 705, 'y': 240}, {'x': 673, 'y': 256}, {'x': 641, 'y': 272}]
    assert [row['turn'] for row in drag_turns] == [5, 9, 11]
    assert all(row['points'] == expected_points for row in drag_turns)
    assert not any(step['op'] == 'pointer_drag' and step['points'] != expected_points
                   for turn in range(1, 13)
                   for step in read(root / f'typed-{turn}.json')['steps'])

    preaction = read(root / 'preaction.json')
    report = {
        'artifact_audit_passed': True,
        'preregistered': True,
        'hard_success': False,
        'formal_finish_outcome': 'unavailable',
        'formal_finish_limit': 'the driver raised at its proposal-loop else branch before consuming the supervisor abort, so no independent finish evaluation was emitted',
        'continuous_independent_observer_outcome': {
            'status': 'partial_A_to_B_only',
            'records': len(observer),
            'unique_states': 2,
            'transition_indices': transitions,
            'stable_final_records': len(observer) - transitions[0],
            'A_to_B_owned_road_tiles': [977, 978, 979],
            'B_to_C_missing_tiles': [1043, 1107],
            'forbidden_tiles_clear': [1041, 1042, 1105, 1106],
            'score': final_score,
            'source': observer_path.relative_to(HERE).as_posix(),
            'source_sha256': sha(observer_path),
        },
        'model_drag_attempts': drag_turns,
        'effect_diagnosis': 'the retained episode contains a stable independent A-to-B construction effect, followed by two repeated drags over the same A-to-B points and no B-to-C drag; full task failure therefore includes missed effect/state progression rather than input-delivery failure alone',
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
        'interpretation': 'the general sign-to-tile instruction did not produce a model verify or safe stop within 12 turns. Formal finish evaluation is unavailable, but the continuous source-pinned observer proves stable partial A-to-B construction and missing B-to-C construction',
        'scope': 'one retained candidate episode; observer evidence proves only its partial tile state, not complete correctness, latency distribution, human tempo, or a general token result',
        'audit_sha256': sha(Path(__file__)),
    }
    (BASE / 'posthoc-audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
