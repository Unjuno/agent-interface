import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image

root = Path(__file__).resolve().parent
load = lambda p: json.loads(p.read_text())
plan = load(root / 'study/PLAN.json')
assert plan['waits_ms'] == [0, 50, 50, 0]
assert plan['seed'] == 991105 and plan['right_count'] == 18
image_links = 0
rows = []
for index, (run, delay, expected_x) in enumerate([
    (root / f'study/run-{i}', delay, x)
    for i, delay, x in ((1, 0, 84), (2, 50, 86), (3, 50, 86), (4, 0, 84))
] + [(root / 'primary', 50, 86)], 1):
    goal = load(run / 'goal.json')
    source = load(run / 'source-1.json')
    with Image.open(run / 'bridge/images' / Path(source['native']['artifact']['path']).name) as image:
        anchor = image.convert('RGB').crop((588, 371, 612, 385)).tobytes()
    assert hashlib.sha256(anchor).hexdigest() == plan['reference_anchor_sha256']
    assert load(run / 'workload.json')['seed'] == 991105
    request = load(run / 'request-1.json')
    assert request['point'] == [600, 378]
    tail = request['tail']
    expected = ([{'op': 'wait_update', 'timeout_ms': delay}] if delay else [])
    expected += [{'op': 'key_chord', 'keys': ['Right']}] * 18
    expected += [{'op': 'wait_update', 'timeout_ms': 50}, {'op': 'key_chord', 'keys': ['CTRL', 's']}]
    assert tail == expected
    actions = load(run / 'actions.json'); assert len(actions) == 1
    action = actions[0]
    assert action['result']['status'] == 'completed'
    execution = action['result']['execution']
    assert execution['emissions'] == 43
    assert all(r['verified'] and r['keys_down'] == r['buttons_down'] == [] for r in execution['releases'])
    programs = list((run / 'bridge').glob('program-*.json')); assert len(programs) == 1
    ops = load(programs[0])['ops']
    assert ops[3] == {'op': 'pointer_button', 'button': 'left', 'down': False}
    assert ops[4:-1] == tail and ops[-1] == {'op': 'release_all'}
    for stage in (1, 2):
        assert load(run / f'reply-{stage}.json')['decision_sha256'] == hashlib.sha256((run / f'request-{stage}.json').read_bytes()).hexdigest()
    final = load(run / 'reply-2.json')
    assert final['status'] == 'finished' and final['evaluation']['success']
    assert final['cleanup']['status'] == 'completed'
    assert all(p['returncode'] is not None for p in final['cleanup']['processes'])
    rects = ET.parse(run / 'shape.svg').getroot().findall('{http://www.w3.org/2000/svg}rect')
    assert len(rects) == 1
    actual = {k: float(rects[0].attrib[k]) for k in ('x', 'y', 'width', 'height')}
    assert actual == {'x': expected_x, 'y': 50, 'width': 40, 'height': 30}
    assert rects[0].attrib.get('transform') is None
    if index == 5:
        assert goal['task']['kind'] == 'move_right_preserve_geometry'
        assert goal['task']['x_greater_than'] == 50.5
        assert goal['task']['dx_meaning'] == 'nominal_drag_screen_px_not_exact_keyboard_displacement'
    def images(value):
        global image_links
        if isinstance(value, dict):
            n = value.get('native')
            if isinstance(n, dict) and 'artifact' in n:
                a = n['artifact']; path = run / 'bridge/images' / Path(a['path']).name
                assert hashlib.sha256(path.read_bytes()).hexdigest() == a['sha256']
                assert a['source_raw_sha256'] == n['sha256'] and value['capture_ns'] == n['capture_started_ns']
                image_links += 1
            for child in value.values(): images(child)
        elif isinstance(value, list):
            for child in value: images(child)
    for file in run.rglob('*.json'): images(load(file))
    rows.append({'run': index, 'delay_ms': delay, 'saved_x': actual['x'],
                 'task_success': True, 'exact_18_nudges': actual['x'] == 86,
                 'program_ms': (execution['ended_ns'] - execution['started_ns']) / 1e6})
manifest = root / 'MANIFEST.json'
if manifest.exists():
    for name, digest in load(manifest).items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
print(json.dumps({'audit': 'pass', 'image_hash_links': image_links, 'rows': rows}, indent=2))
