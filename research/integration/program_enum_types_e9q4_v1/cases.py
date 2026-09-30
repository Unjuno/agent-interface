"""Fixed, JSON-only 140-case compatibility corpus; no runtime imports."""
from copy import deepcopy


def corpus():
    invalid = [[], {}, ['left'], {'name': 'left'}, None, False, True, 0, 1.5, '', 'not-a-member']
    frames = ['screen_physical_px', 'screen_logical', 'window_client']
    fields = [({'op': 'pointer_move', 'x': 0, 'y': 0}, 'frame', frames),
              ({'op': 'observe', 'x': 0, 'y': 0, 'w': 10, 'h': 10}, 'frame', frames),
              ({'op': 'pointer_button', 'down': True}, 'button', ['left', 'middle', 'right', 'x1', 'x2'])]
    prefixes = [[], [{'op': 'key_chord', 'keys': ['F8'], 'repeat': 2}],
                [{'op': 'text', 'text': 'ab', 'gap_ms': 1},
                 {'op': 'key_chord', 'keys': ['F8'], 'repeat': 2}]]
    base = {'schema': 'agent-interface/program-v1', 'program_id': 'enum-case',
            'source': {'observation_seq': 1, 'binding_revision': 1},
            'authority': {'lease_id': 'test-only', 'expires_at_ns': 100},
            'terminal': {'release_all_required': True}}
    result = []
    for prefix in prefixes:
        for template, field, values in fields:
            for value in invalid + values:
                p = deepcopy(base)
                p['ops'] = deepcopy(prefix) + [dict(template, **{field: deepcopy(value)}), {'op': 'release_all'}]
                result.append({'id': len(result), 'program': p, 'control': None})
    for label in ['expired', 'stale_observation', 'stale_binding', 'unsupported', 'permission',
                  'coordinate', 'earlier_error', 'capacity']:
        p = deepcopy(base)
        p['ops'] = [{'op': 'pointer_move', 'frame': 'window_client', 'x': 0, 'y': 0}, {'op': 'release_all'}]
        if label == 'earlier_error':
            p['ops'] = [{'op': 'key_state', 'key': 'F8', 'down': False},
                        {'op': 'observe', 'frame': [], 'x': 0, 'y': 0, 'w': 10, 'h': 10}, {'op': 'release_all'}]
        if label == 'capacity':
            p['ops'] = [{'op': 'wait_update', 'timeout_ms': 0}] * 128 + [{'op': 'release_all'}]
        result.append({'id': len(result), 'program': p, 'control': label})
    assert len(result) == 140
    return result
