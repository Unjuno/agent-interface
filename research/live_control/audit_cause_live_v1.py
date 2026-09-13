"""Audit cause delivery across actual app, raw socket slices, and displayed index."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from decision_receipt_v2 import build
from report_pages_v2 import digest
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    root = HERE / 'results/cause-live-01'
    runtime = root / 'runtime'
    for name, sha in read(root / 'initial/plan.json')['sources'].items():
        assert digest((HERE / name).read_bytes()) == sha
    for name, sha in read(runtime / 'sources.json').items():
        assert digest((HERE.parent / name).read_bytes()) == sha
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    first, recovery = [read(root / name / 'report.json') for name in ('interrupt', 'recover')]
    segments = [{'request': {'after': 0}, 'reply': read(root / 'initial/batch.json')}]
    segments += first['exchanges'] + recovery['exchanges']
    segments.append({'request': read(root / 'finish/request.json'), 'reply': read(root / 'finish/result.json')})
    covered, count = set(), 0
    for item in segments:
        a, b = item['request']['after'], item['reply']['cursor']
        assert item['reply']['status'] == 'boundary'
        assert b - a == len(item['reply']['records'])
        assert item['reply']['records'] == raw[a:b]
        covered.update(range(a, b))
        count += b - a
    assert covered == set(range(len(raw)))
    receipts = []
    for name, report in [('interrupt', first), ('recover', recovery)]:
        receipt = read(root / name / 'receipt.json')
        assert build((root / name / 'report.json').read_bytes()) == receipt
        assert receipt['program_binding']['terminal'] == report['terminal']
        assert receipt['terminals'][-1]['record'] == report['terminal']
        image = receipt['image']
        assert digest((runtime / image['relative_path']).read_bytes()) == image['sha256']
        receipts.append({'program': name, 'json_bytes': len(json.dumps(receipt).encode()),
                         'attention': receipt['detail_review_required']})
    assert receipts[0]['attention'] and not receipts[1]['attention']
    terminal = first['terminal']
    assert terminal['status'] == 'needs_decision' and terminal['steps_completed'] == 1
    assert [e['key'] for e in first['last_reply']['records'] if e['event'] == 'input_admission'] == ['Control_L']
    cause = terminal['interruption']['record']
    assert cause['reason'] == 'focus_changed' and cause['verified']
    assert cause in read(runtime / 'owner-events.json')
    assert cause['verified_ns'] < terminal['release']['verified_ns'] < terminal['terminal_ns']
    assert recovery['terminal']['status'] == 'completed' and recovery['terminal']['interruption'] is None
    assert all(e['release']['verified'] for e in raw if e['event'] == 'terminal')
    injection = read(root / 'interrupt/injection.json')
    assert 'error' not in injection
    assert injection['physical_down_before_transfer'] and injection['physical_up_after_transfer']
    observations = [e for e in raw if e['event'] == 'observation']
    decoder = Decoder('live-control')
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as picture:
            assert (picture.width, picture.height, picture.mode, picture.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    rect = ET.parse(runtime / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    actual = {k: rect.get(k) for k in ('x', 'y', 'width', 'height', 'transform')}
    assert raw[-1]['success'] and actual == raw[-1]['actual'] == {'x': '52', 'y': '50', 'width': '40', 'height': '30', 'transform': None}
    summary = {'audit_sha256': digest(Path(__file__).read_bytes()),
               'source_pins_and_transport_slices_verified': True,
               'cause_preserved_owner_to_terminal_to_socket_to_index': True,
               'unique_events': len(raw), 'received_records': count, 'socket_exchanges': len(segments),
               'exact_frames': len(observations), 'receipts': receipts,
               'task_success': True, 'actual': actual,
               'release_to_terminal_ms': (terminal['terminal_ns'] - cause['verified_ns']) / 1e6,
               'post_release_observations_before_terminal': sum(cause['verified_ns'] < e['capture_ns'] < terminal['terminal_ns'] for e in observations),
               'capture_to_evaluation_seconds': (raw[-1]['known_ns'] - observations[0]['capture_ns']) / 1e9,
               'limits': 'One injected fault with explicit model image/index review and recovery. Timing is local runtime, not model latency/human speed. No model tokens or paired performance comparison. Bridge exit checked separately; no per-child cleanup inventory.'}
    (root / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
