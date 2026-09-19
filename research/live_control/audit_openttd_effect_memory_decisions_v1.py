"""Audit the preregistered fixed-context OpenTTD effect-memory decisions."""
import hashlib
import json
import os
from pathlib import Path

from semantic_checkpoint_v4 import parse


HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-effect-memory-decisions-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(value):
    value = str(value)
    if os.name != 'nt' and len(value) >= 3 and value[1:3] == ':\\':
        return Path('/mnt') / value[0].lower() / value[3:].replace('\\', '/')
    return Path(value)


def events(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def proposal_and_usage(path):
    rows = events(path)
    messages = [row['item']['text'] for row in rows
                if row.get('type') == 'item.completed'
                and row.get('item', {}).get('type') == 'agent_message']
    completions = [row['usage'] for row in rows if row.get('type') == 'turn.completed']
    if len(messages) != 1 or len(completions) != 1:
        raise ValueError('one model message and one usage record required')
    return parse(messages[0], required_turn=5, trees='transparent'), completions[0]


def classify(proposal):
    checkpoint = proposal['checkpoint']
    drags = [step for step in proposal.get('steps', []) if step.get('op') == 'pointer_drag']
    return {
        'kind': proposal['kind'],
        'intent': proposal.get('intent'),
        'checkpoint_status': checkpoint['status'],
        'drag_count': len(drags),
        'drag_points': drags[0]['points'] if len(drags) == 1 else None,
    }


def main():
    preregistration = read(ROOT / 'preregistration.json')
    assert preregistration['status'] == 'preregistered_before_model_execution'
    assert preregistration['sources']['effect_memory'] == sha(HERE / 'openttd_effect_memory_v1.py')
    assert preregistration['sources']['memory_audit'] == sha(HERE / 'audit_openttd_effect_memory_v1.py')
    assert preregistration['sources']['model_runner'] == sha(HERE / 'model_pair_runner_v2.py')
    assert preregistration['sources']['checkpoint_parser'] == sha(HERE / 'semantic_checkpoint_v4.py')

    cases = []
    for case in preregistration['cases']:
        for field in ('prompt', 'baseline_image', 'baseline_typed', 'memory_image'):
            path = local_path(case[field])
            assert path.is_file()
            assert case[field + '_sha256'] == sha(path)
        turn = case['turn']
        baseline_path = local_path(case['baseline_typed'])
        baseline = parse(json.dumps(read(baseline_path)), 5, 'transparent')
        baseline_events = baseline_path.parent / f'model-{turn}' / 'events.jsonl'
        _, baseline_usage = proposal_and_usage(baseline_events)
        output = local_path(case['output'])
        memory, memory_usage = proposal_and_usage(output / 'events.jsonl')
        plan = read(output / 'plan.json')
        process = read(output / 'process.json')
        assert process['exit_code'] == 0
        assert plan['requested_model'] == 'gpt-6-astra' and plan['requested_effort'] == 'medium'
        assert plan['image_sha256'] == case['memory_image_sha256']
        assert sha(output / 'prompt.txt') == case['prompt_sha256']
        cases.append({
            'turn': turn,
            'baseline': classify(baseline),
            'memory': classify(memory),
            'baseline_usage': baseline_usage,
            'memory_usage': memory_usage,
        })

    assert [case['baseline']['checkpoint_status'] for case in cases] == ['uncertain', 'uncertain']
    assert [case['memory']['checkpoint_status'] for case in cases] == ['observed', 'observed']
    assert all(case['memory']['kind'] == 'act' and case['memory']['intent'] == 'progress'
               and case['memory']['drag_count'] == 1 for case in cases)
    assert cases[0]['memory']['drag_points'] == cases[1]['memory']['drag_points']
    assert cases[0]['memory']['drag_points'] != [
        {'x': 704, 'y': 240}, {'x': 672, 'y': 256}, {'x': 640, 'y': 272}]

    total = lambda side, key: sum(case[f'{side}_usage'][key] for case in cases)
    result = {
        'audit_passed': True,
        'preregistered_cases': 2,
        'cases': cases,
        'primary_endpoint': {
            'baseline': {'observed': 0, 'uncertain': 2, 'contradicted': 0},
            'memory': {'observed': 2, 'uncertain': 0, 'contradicted': 0},
        },
        'input_tokens': {
            'baseline': total('baseline', 'input_tokens'),
            'memory': total('memory', 'input_tokens'),
            'difference': total('memory', 'input_tokens') - total('baseline', 'input_tokens'),
        },
        'cached_input_tokens': {
            'baseline': total('baseline', 'cached_input_tokens'),
            'memory': total('memory', 'cached_input_tokens'),
        },
        'live_action_executed': False,
        'decision': 'advance bounded effect memory to a fresh preregistered live episode; do not promote yet',
        'scope': 'two archived contexts and separate model samples; descriptive decision signal, not causal correctness, speed or token evidence',
    }
    (ROOT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
