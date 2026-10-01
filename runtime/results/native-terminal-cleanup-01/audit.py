import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
load = lambda p: json.loads(p.read_text())
links = 0
for index, stage in ((1, 1), (2, 3)):
    run = root / f'run-{index}'
    reply = load(run / f'reply-{stage}.json')
    report = load(run / 'cleanup-report.json')
    assert reply['cleanup'] == report
    assert report['status'] == 'completed' and not report['errors']
    assert report['processes'] == load(run / 'cleanup.json')
    assert len(report['processes']) == 3
    assert all(p['returncode'] is not None for p in report['processes'])
    assert not report['owner_exit_verified'] and not report['descendants_verified']
    for request in run.glob('request-*.json'):
        response = run / request.name.replace('request-', 'reply-')
        assert load(response)['decision_sha256'] == hashlib.sha256(request.read_bytes()).hexdigest()
    def images(value):
        global links
        if isinstance(value, dict):
            native = value.get('native')
            if isinstance(native, dict) and 'artifact' in native:
                artifact = native['artifact']
                path = run / 'bridge/images' / Path(artifact['path']).name
                assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256']
                assert artifact['source_raw_sha256'] == native['sha256']
                assert value['capture_ns'] == native['capture_started_ns']
                links += 1
            for child in value.values(): images(child)
        elif isinstance(value, list):
            for child in value: images(child)
    for path in run.rglob('*.json'): images(load(path))
    if index == 1:
        assert reply['status'] == 'needs_review' and reply['actions'] == []
        assert 'visually flat target region refused' in reply['error']
        assert not list((run / 'bridge').glob('program-*.json'))
    else:
        assert reply['status'] == 'finished' and reply['evaluation']['success']
        rect = next(ET.parse(run / 'shape.svg').getroot().iter('{http://www.w3.org/2000/svg}rect'))
        assert float(rect.attrib['x']) == 86
        actions = load(run / 'actions.json')
        assert [r['interaction'] for r in actions] == ['click', 'keyboard']
        assert all(r['result']['status'] == 'completed' for r in actions)
        assert all(release['verified'] and release['keys_down'] == release['buttons_down'] == []
                   for row in actions for release in row['result']['execution']['releases'])
manifest = root / 'MANIFEST.json'
if manifest.exists():
    for name, digest in load(manifest).items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
print(json.dumps({'audit': 'pass', 'image_hash_links': links,
                  'run_1': 'input_refused_cleanup_completed',
                  'run_2': 'explicit_visual_correction_saved_x86_cleanup_completed'}))
