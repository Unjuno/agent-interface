"""Audit the first fresh live OpenTTD bounded-effect-memory episode."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

from openttd_effect_memory_v1 import build as build_effect_memory
from semantic_checkpoint_v4 import next_checkpoint_turn, parse


HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-09'
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


def current_image(applied):
    observation = applied['result']['state']['continuation']['observation']
    return ROOT / 'runtime' / Path(observation['image']).name


def same_pixels(left, right):
    with Image.open(left) as a, Image.open(right) as b:
        return a.size == b.size and ImageChops.difference(
            a.convert('RGB'), b.convert('RGB')).getbbox() is None


def main():
    prereg = read(BASE / 'preregistration.json')
    assert prereg['status'] == 'preregistered_before_execution'
    for name, expected in prereg['sources'].items():
        assert sha(HERE / name) == expected, name
    for plan_path in (CONTROL / 'plan.json', ROOT / 'plan.json'):
        for name, expected in read(plan_path)['sources'].items():
            assert sha(HERE / name) == expected, name

    result = read(ROOT / 'result.json')
    control_result = read(CONTROL / 'result.json')
    assert result['success'] is True and result['finish_kind'] == 'visual_verify'
    assert result['controller_outcome'] == 'verified_success' and result['exit_code'] == 0
    assert result['proposals_executed'] == 8 and result['journal_calls'] == 34
    assert control_result['success'] is True and control_result['model_turns'] == 9
    evaluation = result['evaluation']
    assert evaluation['success'] is True and evaluation['checks'] == {
        'target_owned_roads': True,
        'ordered_bidirectional_connections': True,
        'forbidden_tiles_clear': True,
        'surrounding_road_owner_unchanged': True,
    }

    turns = read(CONTROL / 'turns.json')
    assert len(turns) == 9 and [row['kind'] for row in turns] == ['act'] * 8 + ['verify']
    required = None
    typed = []
    usage = []
    for turn in range(1, 10):
        rows = [json.loads(line) for line in
                (ROOT / f'model-{turn}/events.jsonl').read_text(encoding='utf-8').splitlines()]
        message = next(row['item']['text'] for row in rows if row.get('type') == 'item.completed')
        proposal = parse(message, required, 'transparent')
        assert proposal == read(ROOT / f'typed-{turn}.json')
        typed.append(proposal)
        usage.append(next(row['usage'] for row in rows if row.get('type') == 'turn.completed'))
        new_required = next_checkpoint_turn(turn, proposal)
        if new_required is not None:
            required = new_required
        elif required is not None and proposal['checkpoint']['status'] == 'observed':
            required = None
    assert required is None
    assert typed[5]['checkpoint']['prior_turn'] == 5 and typed[5]['checkpoint']['status'] == 'uncertain'
    assert typed[6]['checkpoint']['prior_turn'] == 5 and typed[6]['checkpoint']['status'] == 'observed'
    assert typed[7]['checkpoint']['prior_turn'] == 7 and typed[7]['checkpoint']['status'] == 'uncertain'
    assert typed[8]['checkpoint']['prior_turn'] == 7 and typed[8]['checkpoint']['status'] == 'observed'

    drags = [(turn, step) for turn, proposal in enumerate(typed, 1)
             for step in proposal.get('steps', []) if step.get('op') == 'pointer_drag']
    assert [turn for turn, _ in drags] == [5, 7]
    first_points = drags[0][1]['points']
    second_points = drags[1][1]['points']
    assert first_points != second_points
    assert first_points == [
        {'x': 705, 'y': 240}, {'x': 673, 'y': 256}, {'x': 641, 'y': 272}]
    assert second_points == [
        {'x': 641, 'y': 272}, {'x': 673, 'y': 288}, {'x': 705, 'y': 304}]

    replay = []
    effect = None
    with tempfile.TemporaryDirectory(prefix='audit-openttd-memory-') as temporary:
        temporary = Path(temporary)
        for turn in (5, 6, 7, 8):
            applied = read(ROOT / f'applied-{turn}.json')
            destination = temporary / f'planner-{turn + 1}.png'
            planner, effect = build_effect_memory(
                current_image(applied), applied, typed[turn - 1], ROOT / 'runtime',
                destination, effect=effect, turn=turn)
            expected = ROOT / f'planner-{turn + 1}.png'
            assert same_pixels(planner, expected)
            replay.append({
                'after_turn': turn,
                'source_turn': effect['source_turn'],
                'inspection_turns': effect['inspection_turns'],
                'dimensions': list(Image.open(planner).size),
                'checked_in_sha256': sha(expected),
            })
    assert [(row['source_turn'], row['inspection_turns']) for row in replay] == [
        (5, 0), (5, 1), (7, 0), (7, 1)]

    calls = read(ROOT / 'calls.json')
    assert len(calls) == 34
    runtime_events = [json.loads(line) for line in
                      (ROOT / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
    observations = [row for row in runtime_events if row.get('event') == 'observation']
    terminals = [row for row in runtime_events if row.get('event') == 'terminal']
    assert len(observations) == 44 and len(terminals) == 17
    assert all(row['release']['verified'] and not row['release']['keys_down']
               and not row['release']['buttons_down'] for row in terminals)

    observer_path = ROOT / 'runtime/game-stderr.txt'
    observer = observer_records(observer_path)
    assert len(observer) == 171
    transitions = [index for index in range(1, len(observer))
                   if signature(observer[index]) != signature(observer[index - 1])]
    assert transitions == [90, 131]
    transition_tiles = []
    for index in transitions:
        before = {tile['id']: tile for tile in observer[index - 1]['guard']}
        after = {tile['id']: tile for tile in observer[index]['guard']}
        transition_tiles.append([tile for tile in before if before[tile] != after[tile]])
    assert transition_tiles == [[977, 978, 979], [1043, 1107]]
    final_score = score(observer[-1], observer[0])
    assert final_score == {key: evaluation[key] for key in ('success', 'checks', 'changed_surrounding_tiles', 'contract')}
    assert all(signature(row) == signature(observer[-1]) for row in observer[131:])

    input_tokens = sum(row['input_tokens'] for row in usage)
    cached_tokens = sum(row['cached_input_tokens'] for row in usage)
    output_tokens = sum(row['output_tokens'] for row in usage)
    assert (input_tokens, cached_tokens, output_tokens) == (151853, 91392, 1719)
    model_wait_ms = sum(row['model_runner_returned_ns'] - row['model_runner_started_ns']
                        for row in turns) / 1e6
    feedback_ms = sum(row['applied_read_ns'] - row['proposal_published_ns']
                      for row in turns if 'applied_read_ns' in row) / 1e6
    assert model_wait_ms == 131033.9726 and feedback_ms == 19047.7812

    report = {
        'audit_passed': True,
        'preregistered': True,
        'hard_success': True,
        'semantic_outcome': result['controller_outcome'],
        'independent_checks': evaluation['checks'],
        'model_turns': len(turns),
        'input_tokens': input_tokens,
        'cached_input_tokens': cached_tokens,
        'output_tokens': output_tokens,
        'model_wait_ms': model_wait_ms,
        'proposal_to_feedback_ms': feedback_ms,
        'initial_observation_to_semantic_completion_ms':
            control_result['initial_observation_to_semantic_completion']['duration_ns'] / 1e6,
        'durable_calls': len(calls),
        'runtime_exact_frames': len(observations),
        'verified_release_terminals': len(terminals),
        'drag_attempts': [{'turn': turn, **step} for turn, step in drags],
        'repeated_completed_segment_drags': 0,
        'effect_memory_replay': replay,
        'observer': {
            'records': len(observer),
            'transition_indices': transitions,
            'transition_tiles': transition_tiles,
            'stable_complete_records': len(observer) - transitions[-1],
            'score': final_score,
            'source_sha256': sha(observer_path),
        },
        'same_task_summary': {
            'effect_sheet_v7': 'success in 7 turns',
            'unchanged_replication_v8': 'safe-stop failure in 8 turns',
            'bounded_effect_memory_v9': 'success in 9 turns',
        },
        'decision': 'RETAIN_LIVE_EFFECT_MEMORY_FOR_REPLICATION;_DO_NOT_PROMOTE',
        'scope': 'one fresh same-task live episode; no causal speed, token, changed-geometry, human-tempo or cross-domain claim',
        'audit_sha256': sha(Path(__file__)),
    }
    (BASE / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
