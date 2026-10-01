import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
load = lambda p: json.loads(p.read_text())
canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
request = load(root / 'run/request-1.json')
flat = load(root / 'flat-reference-request.json')
program_path, = (root / 'run/bridge').glob('program-*.json')
program = load(program_path)
expected_tail = [{'op': 'wait_update', 'timeout_ms': 50}]
expected_tail += [{'op': 'key_chord', 'keys': ['Right']} for _ in range(18)]
expected_tail += [{'op': 'wait_update', 'timeout_ms': 50}, {'op': 'key_chord', 'keys': ['CTRL', 's']}]

def check_plan(compact, expanded):
    assert compact == dict(flat, tail=[expected_tail[0],
        {'op': 'key_chord', 'keys': ['Right'], 'repeat': 18}, *expected_tail[-2:]])
    assert flat['tail'] == expected_tail
    assert expanded['ops'] == [{'op': 'focus', 'target': 'app'},
        {'op': 'pointer_move', 'frame': 'screen_physical_px', 'x': 600, 'y': 378},
        {'op': 'pointer_button', 'button': 'left', 'down': True},
        {'op': 'pointer_button', 'button': 'left', 'down': False},
        *expected_tail, {'op': 'release_all'}]

check_plan(request, program)
corrupt = []
bad_count = copy.deepcopy(request); bad_count['tail'][1]['repeat'] = 17
corrupt.append((bad_count, program))
bad_order = copy.deepcopy(program); bad_order['ops'][4], bad_order['ops'][5] = bad_order['ops'][5], bad_order['ops'][4]
corrupt.append((request, bad_order))
bad_rows = copy.deepcopy(program); bad_rows['ops'].pop(6)
corrupt.append((request, bad_rows))
for changed_request, changed_program in corrupt:
    try: check_plan(changed_request, changed_program)
    except AssertionError: pass
    else: raise AssertionError('corruption was accepted')
for name, digest in load(root / 'SOURCE_FREEZE.json').items():
    assert hashlib.sha256((root / 'source' / Path(name).name).read_bytes()).hexdigest() == digest
for stage in (1, 2):
    assert load(root / f'run/reply-{stage}.json')['decision_sha256'] == hashlib.sha256((root / f'run/request-{stage}.json').read_bytes()).hexdigest()
final = load(root / 'run/reply-2.json')
assert final['status'] == 'finished' and final['evaluation']['success']
assert final['cleanup']['status'] == 'completed'
assert all(p['returncode'] is not None for p in final['cleanup']['processes'])
rect, = ET.parse(root / 'run/shape.svg').getroot().findall('{http://www.w3.org/2000/svg}rect')
assert {k: rect.attrib[k] for k in ('x','y','width','height')} == {'x':'86','y':'50','width':'40','height':'30'}
actions = load(root / 'run/actions.json'); assert len(actions) == 1
result = actions[0]['result']; assert result['status'] == 'completed'
assert result['execution']['emissions'] == 43
assert all(r['verified'] and r['keys_down'] == r['buttons_down'] == [] for r in result['execution']['releases'])
links = 0
def images(value):
    global links
    if isinstance(value, dict):
        n = value.get('native')
        if isinstance(n, dict) and 'artifact' in n:
            a = n['artifact']; path = root / 'run/bridge/images' / Path(a['path']).name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == a['sha256']
            assert a['source_raw_sha256'] == n['sha256'] and value['capture_ns'] == n['capture_started_ns']
            links += 1
        for child in value.values(): images(child)
    elif isinstance(value, list):
        for child in value: images(child)
for path in (root / 'run').rglob('*.json'): images(load(path))
if (root / 'MANIFEST.json').exists():
    for name, digest in load(root / 'MANIFEST.json').items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
print(json.dumps({'audit': 'pass', 'decision_bytes_flat': len(canonical(flat)),
    'decision_bytes_compact': len(canonical(request)), 'expanded_ops': len(program['ops']),
    'image_hash_links': links, 'corruption_controls_rejected': len(corrupt),
    'disposition': 'PASS_NATIVE_REPEAT_SCOPED', 'model_token_benefit': 'unmeasured'}, indent=2))
