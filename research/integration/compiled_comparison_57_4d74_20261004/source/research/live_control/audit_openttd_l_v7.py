"""Audit the preregistered live OpenTTD bounded drag-effect allocation."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

from semantic_checkpoint_v4 import next_checkpoint_turn, parse


HERE = Path(__file__).resolve().parent
BASE = HERE / 'results/timing-envelope-openttd-l-07'
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
    result = read(CONTROL / 'result.json')
    assert result['success'] and result['exit_code'] == 0 and result['model_turns'] == 7
    driver_result = read(ROOT / 'result.json')
    assert driver_result['exit_code'] == 0 and driver_result['proposals_executed'] == 6
    evaluation = next(row for row in read(ROOT / 'finish.json')['reply']['records']
                      if row['event'] == 'independent_evaluation')
    assert evaluation['success'] and all(evaluation['checks'].values())
    assert evaluation['changed_surrounding_tiles'] == []

    turns = read(CONTROL / 'turns.json')
    assert len(turns) == 7
    assert [row['kind'] for row in turns] == ['act'] * 6 + ['verify']
    required = None
    usage = []
    typed = []
    for turn in range(1, 8):
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
    assert required is None
    assert typed[5]['checkpoint']['prior_turn'] == 5 and typed[5]['checkpoint']['status'] == 'observed'
    assert typed[6]['checkpoint']['prior_turn'] == 6 and typed[6]['checkpoint']['status'] == 'observed'

    drags = []
    for turn, proposal in enumerate(typed, 1):
        for step in proposal.get('steps', []):
            if step.get('op') == 'pointer_drag':
                drags.append({'turn': turn, 'points': step['points'], 'duration_ms': step['duration_ms']})
    assert [row['turn'] for row in drags] == [5, 6]
    assert drags[0]['points'] == [
        {'x': 705, 'y': 240}, {'x': 673, 'y': 256}, {'x': 641, 'y': 272}]
    assert drags[1]['points'] == [
        {'x': 641, 'y': 272}, {'x': 673, 'y': 288}, {'x': 705, 'y': 304}]

    sheets = []
    for next_turn in (6, 7):
        path = ROOT / f'planner-{next_turn}.png'
        with Image.open(path) as image:
            dimensions = list(image.size)
        assert dimensions == [1280, 1046]
        sheets.append({'next_turn': next_turn, 'path': path.name,
                       'dimensions': dimensions, 'sha256': sha(path)})

    calls = read(ROOT / 'calls.json')
    assert len(calls) == 26
    assert driver_result['journal_calls'] == len(calls)
    assert [call['result']['request']['command']['op'] for call in calls[:2]] == ['clock', 'submit']
    for index in range(6):
        group = calls[2 + index * 4:2 + (index + 1) * 4]
        assert [call['result']['request']['command']['op'] for call in group] == ['clock', 'submit', 'clock', 'submit']
    runtime_events = [json.loads(line) for line in (ROOT / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
    observations = [row for row in runtime_events if row.get('event') == 'observation']
    terminals = [row for row in runtime_events if row.get('event') == 'terminal']
    assert len(observations) == 32 and len(terminals) == 13
    assert all(row['release']['verified'] and not row['release']['keys_down'] and
               not row['release']['buttons_down'] for row in terminals)

    observer_path = ROOT / 'runtime/game-stderr.txt'
    observer = observer_records(observer_path)
    assert len(observer) == 122
    transitions = [index for index in range(1, len(observer))
                   if signature(observer[index]) != signature(observer[index - 1])]
    assert transitions == [88, 105]
    transition_changes = []
    for index in transitions:
        before = {tile['id']: tile for tile in observer[index - 1]['guard']}
        after = {tile['id']: tile for tile in observer[index]['guard']}
        transition_changes.append([tile for tile in before if before[tile] != after[tile]])
    assert transition_changes == [[977, 978, 979], [1043, 1107]]
    observer_score = score(observer[-1], observer[0])
    assert observer_score['success'] and observer_score['checks'] == evaluation['checks']
    assert all(signature(row) == signature(observer[-1]) for row in observer[105:])

    input_tokens = sum(row['input_tokens'] for row in usage)
    cached_tokens = sum(row['cached_input_tokens'] for row in usage)
    output_tokens = sum(row['output_tokens'] for row in usage)
    assert (input_tokens, cached_tokens, output_tokens) == (116879, 52224, 1202)
    model_wait_ms = sum(row['model_runner_returned_ns'] - row['model_runner_started_ns'] for row in turns) / 1e6
    feedback_ms = sum(row['applied_read_ns'] - row['proposal_published_ns']
                      for row in turns if 'applied_read_ns' in row) / 1e6
    assert model_wait_ms == 94221.0513 and feedback_ms == 12439.2257
    whole_ms = result['initial_observation_to_semantic_completion']['duration_ns'] / 1e6
    assert whole_ms == 109034.2746

    baseline = prereg['comparison_baseline']
    report = {
        'audit_passed': True,
        'preregistered': True,
        'hard_success': True,
        'independent_checks': evaluation['checks'],
        'model_turns': len(turns),
        'input_tokens': input_tokens,
        'cached_input_tokens': cached_tokens,
        'output_tokens': output_tokens,
        'model_wait_ms': model_wait_ms,
        'proposal_to_feedback_ms': feedback_ms,
        'initial_observation_to_semantic_completion_ms': whole_ms,
        'durable_calls': len(calls),
        'runtime_exact_frames': len(observations),
        'verified_release_terminals': len(terminals),
        'drag_attempts': drags,
        'repeated_same_A_to_B_drags_after_first_effect': 0,
        'effect_sheets': sheets,
        'observer': {
            'records': len(observer),
            'transition_indices': transitions,
            'transition_tiles': transition_changes,
            'stable_final_records': len(observer) - transitions[-1],
            'score': observer_score,
            'source_sha256': sha(observer_path),
        },
        'descriptive_baseline_delta': {
            'baseline_study': baseline['study'],
            'hard_success': [baseline['hard_success'], True],
            'model_turns': [baseline['model_turns'], len(turns)],
            'model_turn_reduction': baseline['model_turns'] - len(turns),
            'input_tokens': [baseline['input_tokens'], input_tokens],
            'input_token_reduction': baseline['input_tokens'] - input_tokens,
            'repeated_same_A_to_B_drags': [baseline['repeated_same_A_to_B_drags'], 0],
        },
        'decision': 'RETAIN_FOR_REPLICATION',
        'interpretation': 'the first fresh effect-sheet episode recognizes A-to-B, proceeds directly to B-to-C and passes the independent five-tile L score in seven turns',
        'scope': 'one sequential same-task episode; no causal percentage, latency distribution, geometry transfer, human-tempo or general token claim',
        'audit_sha256': sha(Path(__file__)),
    }
    (BASE / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
