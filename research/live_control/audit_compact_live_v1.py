"""Audit actual compact review, preserved interruption, recovery and overlaps."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from decision_receipt_v2 import build
from report_pages_v2 import digest
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    root = HERE / 'results/compact-live-01'
    runtime = root / 'runtime'
    for name, sha in read(root / 'initial/plan.json')['sources'].items():
        assert digest((HERE / name).read_bytes()) == sha
    for name, sha in read(runtime / 'sources.json').items():
        assert digest((HERE.parent / name).read_bytes()) == sha
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    segments = []
    for stage in ('initial', 'move', 'finish'):
        for path in sorted((root / stage).glob('query-*-request.json')):
            segments.append({'request': read(path), 'reply': read(path.with_name(path.name.replace('-request', '-reply')))})
    first = read(root / 'move/original-report.json')
    recovery = read(root / 'reviewed-recovery/report.json')
    segments += recovery['exchanges']
    covered, count = set(), 0
    for item in segments:
        a, b = item['request']['after'], item['reply']['cursor']
        assert b - a == len(item['reply']['records'])
        assert item['reply']['records'] == raw[a:b]
        covered.update(range(a, b))
        count += b - a
    assert covered == set(range(len(raw)))
    receipts = []
    for name, path in [('move', root / 'move/original-report.json'), ('reviewed-recovery', root / 'reviewed-recovery/report.json')]:
        receipt = read(root / name / 'receipt.json')
        assert build(path.read_bytes()) == receipt
        assert receipt['program_binding'] is not None
        image = receipt['image']
        assert digest((runtime / image['relative_path']).read_bytes()) == image['sha256']
        receipts.append({'program': name, 'bytes': len(json.dumps(receipt).encode()), 'attention': receipt['detail_review_required']})
    assert receipts[0]['attention'] and not receipts[1]['attention']
    assert first['terminal']['status'] == 'needs_decision' and first['terminal']['steps_completed'] == 1
    assert not any(e.get('event') == 'input_admission' for e in first['last_reply']['records'])
    assert recovery['terminal']['status'] == 'completed'
    assert all(e['release']['verified'] for e in raw if e['event'] == 'terminal')
    owner = read(runtime / 'owner-events.json')
    focus = [e for e in owner if e['reason'] == 'focus_changed']
    assert len(focus) == 1 and focus[0]['verified_ns'] < first['terminal']['terminal_ns']
    observations = [e for e in raw if e['event'] == 'observation']
    decoder = Decoder('live-control')
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as picture:
            assert (picture.width, picture.height, picture.mode, picture.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    rect = ET.parse(runtime / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    actual = {key: rect.get(key) for key in ('x', 'y', 'width', 'height', 'transform')}
    assert raw[-1]['success'] and actual == raw[-1]['actual'] == {'x': '52', 'y': '50', 'width': '40', 'height': '30', 'transform': None}
    summary = {'audit_sha256': digest(Path(__file__).read_bytes()),
               'recovery_source_sha256_post_execution': digest((HERE / 'compact_recover_v1.py').read_bytes()),
               'unique_events': len(raw), 'received_records': count, 'socket_exchanges': len(segments),
               'exact_frames': len(observations), 'receipts': receipts, 'focus_release': focus[0],
               'capture_to_evaluation_seconds': (raw[-1]['known_ns'] - observations[0]['capture_ns']) / 1e9,
               'first_terminal_to_recovery_admission_seconds': (next(e['accepted_ns'] for e in recovery['last_reply']['records'] if e['event'] == 'accepted') - first['terminal']['terminal_ns']) / 1e9,
               'task_success': True, 'presentation': read(root / 'presentation.json'),
               'limits': 'Recovery source hash recorded after execution, unlike initial pinned sources. Overlapping finish reply retained. Model identity/tokens/receipt unavailable; old fixture has no per-child cleanup report. No paired speed inference.'}
    (root / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
