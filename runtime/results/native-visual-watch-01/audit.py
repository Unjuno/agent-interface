"""Read-only retained-evidence audit; does not invoke the watch implementation."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
links = 0


def load(path):
    return json.loads(path.read_text())


def inspect_images(value, images):
    global links
    if isinstance(value, dict):
        native = value.get('native')
        if isinstance(native, dict) and 'artifact' in native:
            artifact = native['artifact']
            path = images/Path(artifact['path']).name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256']
            assert artifact['source_raw_sha256'] == native['sha256']
            assert value['capture_ns'] == native['capture_started_ns']
            links += 1
        for child in value.values():
            inspect_images(child, images)
    elif isinstance(value, list):
        for child in value:
            inspect_images(child, images)


summary = {'runs': [], 'claims': 'scoped primary-assistant use; not formal sensor acceptance'}
for index in (1, 2):
    run = ROOT/f'run-{index}'
    images = run/'bridge/images'
    for path in run.rglob('*.json'):
        inspect_images(load(path), images)
    for request in run.glob('request-*.json'):
        stage = request.stem.split('-')[-1]
        reply = load(run/f'reply-{stage}.json')
        assert reply['decision_sha256'] == hashlib.sha256(request.read_bytes()).hexdigest()
        assert load(request)['source_sequence'] == load(run/f'source-{stage}.json')['sequence']
    assert all(row['returncode'] is not None for row in load(run/'cleanup.json'))
    actions = load(run/'actions.json')
    if index == 2:
        assert len(actions) == 1 and actions[0]['result']['status'] == 'release_unverified'
        assert actions[0]['result']['recovery_required'] is True
        assert 'visual_watch' not in actions[0]
        assert actions[0]['result']['execution']['releases'][0]['verified'] is False
        assert not (run/'request-2.json').exists()
        summary['runs'].append({'run': 2, 'status': 'STOP_before_watch', 'reason': 'release_unverified'})
        continue
    assert len(actions) == 2
    watches = []
    for action in actions:
        assert action['result']['status'] == 'completed'
        assert all(r['verified'] and not r['keys_down'] and not r['buttons_down']
                   for r in action['result']['execution']['releases'])
        watch = action['visual_watch']
        assert watch['status'] == 'changed' and watch['task_success'] is None
        assert not watch['authority_granted'] and not watch['input_dispatched']
        baseline = Image.open(images/Path(watch['source']['native']['artifact']['path']).name).convert('RGB')
        expected_events = []
        previous = {}
        for sample in watch['samples']:
            observation = sample['observation']
            assert observation['pointer_binding'] == watch['source']['pointer_binding']
            current = Image.open(images/Path(observation['native']['artifact']['path']).name).convert('RGB')
            for region, lane in zip(watch['regions'], sample['lanes'], strict=True):
                before = np.asarray(baseline.crop(region['box']))
                after = np.asarray(current.crop(region['box']))
                count = int(np.count_nonzero(np.any(before != after, axis=2)))
                assert lane == {'id': region['id'], 'changed_pixels': count,
                                'condition': count >= region['min_changed_pixels']}
                if previous.get(lane['id']) != lane['condition']:
                    expected_events.append(dict(lane, event_index=len(expected_events)+1,
                        observation_sequence=observation['sequence'], capture_ns=observation['capture_ns'],
                        known_ns=sample['known_ns']))
                previous[lane['id']] = lane['condition']
        assert watch['events'] == expected_events
        assert watch['latest'] == watch['samples'][-1]['lanes']
        watches.append({'stage': action['stage'], 'samples': len(watch['samples']),
                        'latest': watch['latest'],
                        'watch_ms': (watch['ended_ns']-watch['started_ns'])/1e6,
                        'first_changed_known_after_action_started_ms':
                        (next(e['known_ns'] for e in watch['events'] if e['condition'])-action['started_ns'])/1e6})
    rect = ET.parse(run/'shape.svg').find('.//{http://www.w3.org/2000/svg}rect')
    assert [float(rect.get(k)) for k in ('x', 'y', 'width', 'height')] == [80, 50, 40, 30]
    assert rect.get('transform') is None
    assert load(run/'reply-3.json')['status'] == 'finished'
    summary['runs'].append({'run': 1, 'status': 'scoped_pass', 'saved_x': 80, 'watches': watches})
summary['image_hash_links'] = links
print(json.dumps(summary, indent=2))
