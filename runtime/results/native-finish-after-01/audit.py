import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
load = lambda p: json.loads(p.read_text())
links = 0
for name, expected_x, expected_success in [('success', 86, True), ('task-failure', 50, False), ('invalid', 50, None)]:
    run = root / name
    assert len(list(run.glob('request-*.json'))) == len(list(run.glob('reply-*.json'))) == 1
    assert not (run / 'source-2.json').exists()
    request = load(run / 'request-1.json')
    reply = load(run / 'reply-1.json')
    def check_link(value):
        assert value['decision_sha256'] == hashlib.sha256((run / 'request-1.json').read_bytes()).hexdigest()
    check_link(reply)
    bad = copy.deepcopy(reply); bad['decision_sha256'] = '0' * 64
    try: check_link(bad)
    except AssertionError: pass
    else: raise AssertionError('bad request link accepted')
    assert reply['cleanup']['status'] == 'completed' and not reply['cleanup']['errors']
    assert all(p['returncode'] is not None for p in reply['cleanup']['processes'])
    rect, = ET.parse(run / 'shape.svg').getroot().findall('{http://www.w3.org/2000/svg}rect')
    assert float(rect.attrib['x']) == expected_x
    if expected_success is None:
        assert reply['status'] == 'needs_review' and reply['actions'] == []
        assert 'finish_after must be a boolean' in reply['error']
        assert not list((run / 'bridge').glob('program-*.json'))
    else:
        assert request['finish_after'] is True
        assert reply['status'] == 'finished' and reply['finish_mode'] == 'after_action'
        assert reply['evaluation']['success'] is expected_success
        assert reply['observation'] == reply['action']['window_review']['observation']
        assert reply['observation']['capture_ns'] < reply['evaluation']['known_ns'] < reply['cleanup']['ended_ns']
        actions = load(run / 'actions.json'); assert actions == [reply['action']]
        execution = reply['action']['result']['execution']
        assert all(r['verified'] and r['keys_down'] == r['buttons_down'] == [] for r in execution['releases'])
        program_path, = (run / 'bridge').glob('program-*.json')
        if name == 'success':
            baseline_path, = (root / 'baseline').glob('program-*.json')
            assert load(program_path)['ops'] == load(baseline_path)['ops']
            assert len(load(program_path)['ops']) == 26 and execution['emissions'] == 43
            assert dict(load(root / 'baseline/request-1.json'), finish_after=True) == request
        def check_image(value):
            artifact = value['observation']['native']['artifact']
            path = run / 'bridge/images' / Path(artifact['path']).name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256']
        check_image(reply)
        bad = copy.deepcopy(reply); bad['observation']['native']['artifact']['sha256'] = '0' * 64
        try: check_image(bad)
        except AssertionError: pass
        else: raise AssertionError('bad image link accepted')
    def images(value):
        global links
        if isinstance(value, dict):
            n = value.get('native')
            if isinstance(n, dict) and 'artifact' in n:
                a = n['artifact']; path = run / 'bridge/images' / Path(a['path']).name
                assert hashlib.sha256(path.read_bytes()).hexdigest() == a['sha256']
                assert a['source_raw_sha256'] == n['sha256'] and value['capture_ns'] == n['capture_started_ns']
                links += 1
            for child in value.values(): images(child)
        elif isinstance(value, list):
            for child in value: images(child)
    for path in run.rglob('*.json'): images(load(path))
for name, digest in load(root / 'SOURCE_FREEZE.json')['files'].items():
    assert hashlib.sha256((root / 'source' / Path(name).name).read_bytes()).hexdigest() == digest
if (root / 'MANIFEST.json').exists():
    for name, digest in load(root / 'MANIFEST.json').items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
assert len(list((root / 'baseline').glob('request-*.json'))) == 2
print(json.dumps({'audit': 'pass', 'disposition': 'PASS_NATIVE_FINISH_AFTER_SCOPED',
    'requests_baseline': 2, 'requests_finish_after': 1, 'image_hash_links': links,
    'task_failure_preserved': True, 'invalid_flag_no_program': True,
    'corruption_controls_rejected': 5, 'causal_latency_benefit': 'unmeasured'}, indent=2))
