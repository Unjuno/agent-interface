"""Replay the retained v8 drag and inspections through bounded effect memory."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from openttd_effect_memory_v1 import build


HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/timing-envelope-openttd-l-08/fixed-astra'
OUT = HERE / 'results/openttd-effect-memory-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current(applied):
    observation = applied['result']['state']['continuation']['observation']
    return SOURCE / 'runtime' / Path(observation['image']).name


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    states = []
    effect = None
    for turn in (5, 6, 7):
        applied = read(SOURCE / f'applied-{turn}.json')
        proposal = read(SOURCE / f'typed-{turn}.json')
        destination = OUT / f'replayed-planner-{turn + 1}.png'
        planner, effect = build(
            current(applied), applied, proposal, SOURCE / 'runtime', destination,
            effect=effect, turn=turn)
        states.append({
            'after_turn': turn,
            'planner': planner.name,
            'dimensions': list(Image.open(planner).size),
            'sha256': sha(planner),
            'effect': effect,
        })

    assert [state['effect']['source_turn'] for state in states] == [5, 5, 5]
    assert [state['effect']['inspection_turns'] for state in states] == [0, 1, 2]
    assert len({tuple(state['effect']['crop_box']) for state in states}) == 1
    assert states[0]['effect']['before_image'] == states[2]['effect']['before_image']
    assert states[0]['effect']['after_image'] == states[2]['effect']['after_image']
    assert states[0]['dimensions'] == [1280, 1046]
    assert states[1]['dimensions'] == [1280, 1171]
    assert states[2]['dimensions'] == [1280, 1171]

    no_effect_applied = read(SOURCE / 'applied-4.json')
    no_effect_proposal = read(SOURCE / 'typed-4.json')
    planner, empty = build(
        current(no_effect_applied), no_effect_applied, no_effect_proposal,
        SOURCE / 'runtime', OUT / 'no-effect.png')
    assert empty is None and Path(planner).is_file()

    malformed_rejected = 0
    for malformed in ({}, {**effect, 'crop_box': [-1, 0, 2, 2]},
                      {**effect, 'before_image': '../outside.png'}):
        try:
            build(current(no_effect_applied), no_effect_applied, no_effect_proposal,
                  SOURCE / 'runtime', OUT / 'invalid.png', effect=malformed, turn=8)
        except ValueError:
            malformed_rejected += 1
    assert malformed_rejected == 3

    result = {
        'audit_passed': True,
        'source_run': 'timing-envelope-openttd-l-08/fixed-astra',
        'replayed_turns': [5, 6, 7],
        'states': states,
        'malformed_effect_memories_rejected': malformed_rejected,
        'bounded_memory': 'one unresolved drag; original before/after plus latest inspection',
        'semantic_limit': 'presentation evidence only; independent engine scoring remains authoritative',
        'sources': {
            'implementation': sha(HERE / 'openttd_effect_memory_v1.py'),
            'frozen_applied_5': sha(SOURCE / 'applied-5.json'),
            'frozen_applied_6': sha(SOURCE / 'applied-6.json'),
            'frozen_applied_7': sha(SOURCE / 'applied-7.json'),
        },
    }
    (OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
