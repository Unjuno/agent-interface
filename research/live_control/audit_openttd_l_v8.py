"""Audit the first unchanged effect-sheet replication, including its safe-stop outcome."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

from semantic_checkpoint_v4 import next_checkpoint_turn, parse


HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-08'
ROOT = BASE / 'fixed-astra'
CONTROL = BASE / 'fixed-astra-control'
sys.path.insert(0, str(HERE.parent / 'openttd_task'))
from guarded_l_score_v1 import score  # noqa: E402


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def observer_records(path):
    records = []
    for line in path.read_text(encoding='utf-8').splitlines():
        marker = line.find('AIT ')
        if marker >= 0:
            records.append(json.loads(line[marker + 4:]))
    return records


def signature(record):
    return tuple((tile['id'], tile['road'], tile['owner']) for tile in record['guard'])


def main():
    prereg = read(BASE / 'preregistration.json')
    assert prereg['status'] == 'PREREGISTERED_BEFORE_EXECUTION'
    for name, expected in prereg['sources'].items():
        path = HERE.parent / name if name.startswith('openttd_task/') else HERE / name
        assert sha(path) == expected, name
    plan = read(CONTROL / 'plan.json')
    for name, expected in plan['sources'].items():
        assert sha(HERE / name) == expected, name

    error = read(CONTROL / 'error.json')
    assert error['type'] == 'RuntimeError' and error['automatic_retry'] is False
    assert error['detail'].startswith('model stopped: ')
    failure = read(ROOT / 'failure-evaluation.json')
    assert not failure['success'] and failure['exit_code'] == 0
    assert failure['proposals_executed'] == 7 and failure['journal_calls'] == 30
    assert failure['reason'].startswith('typed model safe stop: ')
    assert failure['failure_mode'] == 'bounded_turn_limit'
    evaluation = failure['evaluation']
    assert not evaluation['success']
    assert evaluation['checks'] == {
        'target_owned_roads': False,
        'ordered_bidirectional_connections': False,
        'forbidden_tiles_clear': True,
        'surrounding_road_owner_unchanged': True,
    }

    turns = read(CONTROL / 'turns.json')
    assert len(turns) == 8 and [row['kind'] for row in turns] == ['act'] * 7 + ['stop']
    required = None
    usage = []
    typed = []
    for turn in range(1, 9):
        events = [json.loads(line) for line in (ROOT / f'model-{turn}/events.jsonl').read_text(encoding='utf-8').splitlines()]
        message = next(row['item']['text'] for row in events if row.get('type') == 'item.completed')
        proposal = parse(message, required, 'transparent')
        assert proposal == read(ROOT / f'typed-{turn}.json')
        typed.append(proposal)
        usage.append(next(row['usage'] for row in events if row.get('type') == 'turn.completed'))
        new_required = next_checkpoint_turn(turn, proposal)
        if new_required is not None:
            required = new_required
        elif required is not None and proposal['checkpoint']['status'] == 'observed':
            required = None
    assert required == 5
    assert [typed[index]['checkpoint']['status'] for index in (5, 6, 7)] == ['uncertain'] * 3
    assert typed[7]['kind'] == 'stop'
    drags = [(turn, step) for turn, proposal in enumerate(typed, 1)
             for step in proposal.get('steps', []) if step.get('op') == 'pointer_drag']
    assert len(drags) == 1 and drags[0][0] == 5
    assert drags[0][1]['points'] == [
        {'x': 704, 'y': 240}, {'x': 672, 'y': 256}, {'x': 640, 'y': 272}]

    dimensions = []
    for turn in (6, 7, 8):
        path = ROOT / f'planner-{turn}.png'
        with Image.open(path) as image:
            size = list(image.size)
        dimensions.append({'turn': turn, 'size': size, 'sha256': sha(path)})
    assert [row['size'] for row in dimensions] == [[1280, 1046], [1280, 925], [1280, 925]]

    calls = read(ROOT / 'calls.json')
    assert len(calls) == 30
    runtime_events = [json.loads(line) for line in (ROOT / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
    observations = [row for row in runtime_events if row.get('event') == 'observation']
    terminals = [row for row in runtime_events if row.get('event') == 'terminal']
    assert len(observations) == 32 and len(terminals) == 15
    assert all(row['release']['verified'] and not row['release']['keys_down'] and
               not row['release']['buttons_down'] for row in terminals)

    observer_path = ROOT / 'runtime/game-stderr.txt'
    observer = observer_records(observer_path)
    assert len(observer) == 147
    transitions = [index for index in range(1, len(observer))
                   if signature(observer[index]) != signature(observer[index - 1])]
    assert transitions == [82]
    before = {tile['id']: tile for tile in observer[81]['guard']}
    after = {tile['id']: tile for tile in observer[82]['guard']}
    assert [tile for tile in before if before[tile] != after[tile]] == [977, 978, 979]
    final_score = score(observer[-1], observer[0])
    assert not final_score['success'] and final_score['checks'] == evaluation['checks']
    assert all(signature(row) == signature(observer[-1]) for row in observer[82:])

    input_tokens = sum(row['input_tokens'] for row in usage)
    cached_tokens = sum(row['cached_input_tokens'] for row in usage)
    output_tokens = sum(row['output_tokens'] for row in usage)
    assert (input_tokens, cached_tokens, output_tokens) == (133041, 91392, 1475)
    model_wait_ms = sum(row['model_runner_returned_ns'] - row['model_runner_started_ns'] for row in turns) / 1e6
    feedback_ms = sum(row['applied_read_ns'] - row['proposal_published_ns']
                      for row in turns if 'applied_read_ns' in row) / 1e6
    assert model_wait_ms == 116213.2424 and feedback_ms == 13184.5174

    report = {
        'audit_passed': True,
        'preregistered': True,
        'hard_success': False,
        'semantic_outcome': 'typed_model_safe_stop_after_unresolved_A_to_B_effect',
        'raw_failure_mode': failure['failure_mode'],
        'raw_failure_mode_defect': 'openttd_finish_outcome_v1 maps every abort.json to bounded_turn_limit even when the persisted reason is a typed model safe stop',
        'independent_checks': evaluation['checks'],
        'model_turns': len(turns),
        'input_tokens': input_tokens,
        'cached_input_tokens': cached_tokens,
        'output_tokens': output_tokens,
        'model_wait_ms': model_wait_ms,
        'proposal_to_feedback_ms': feedback_ms,
        'durable_calls': len(calls),
        'runtime_exact_frames': len(observations),
        'verified_release_terminals': len(terminals),
        'drag_attempts': [{'turn': drags[0][0], **drags[0][1]}],
        'repeated_same_A_to_B_drags_after_first_effect': 0,
        'pending_checkpoint_at_stop': required,
        'planner_evidence': dimensions,
        'observer': {
            'records': len(observer),
            'transition_indices': transitions,
            'transition_tiles': [[977, 978, 979]],
            'stable_partial_records': len(observer) - transitions[0],
            'score': final_score,
            'source_sha256': sha(observer_path),
        },
        'replication_summary': {
            'effect_candidate_same_task': {'successes': 1, 'episodes': 2},
            'zero_repeated_completed_A_to_B_drag': {'episodes': 2, 'passes': 2},
            'v7_next_action_after_effect': 'observed_then_build_B_to_C',
            'v8_next_actions_after_effect': 'uncertain_then_two_inspections_then_safe_stop',
        },
        'decision': 'HOLD_EFFECT_SHEET;_ADD_OCCLUSION_RECOVERY_AND_TYPED_STOP_OUTCOME',
        'scope': 'first unchanged same-task replication; no retry, causal speed, geometry transfer, human-tempo or general token claim',
        'audit_sha256': sha(Path(__file__)),
    }
    (BASE / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
