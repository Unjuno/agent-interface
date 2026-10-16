"""Audit first actual paged live result and its presentation overhead."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from report_pages_v2 import reconstruct, wire, digest
from pointer_report_view_v1 import unpack
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    root = HERE / 'results/paged-live-01'
    runtime = root / 'runtime'
    plan = read(root / 'initial/plan.json')
    for name, expected in plan['sources'].items():
        assert digest((HERE / name).read_bytes()) == expected
    for name, expected in read(runtime / 'sources.json').items():
        assert digest((HERE.parent / name).read_bytes()) == expected
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    cursor, received, exchanges = 0, [], 0
    for stage in ('initial', 'move', 'finish'):
        for request in sorted((root / stage).glob('query-*-request.json')):
            q = read(request)
            r = read(request.with_name(request.name.replace('-request', '-reply')))
            assert q['after'] == cursor
            cursor += len(r['records'])
            assert cursor == r['cursor']
            received += r['records']
            exchanges += 1
    assert received == raw
    directories = sorted(root.glob('page-*'), key=lambda p: int(p.name[5:]))
    pages = [read(root / 'move/result.json')['page']] + [read(p / 'result.json') for p in directories]
    view_bytes = (root / 'move/view.json').read_bytes()
    assert reconstruct(pages) == view_bytes
    assert all(len(wire(p)) <= 4096 and not p['starts_mid_line'] and not p['ends_mid_line'] for p in pages)
    assert all(not list(p.glob('query-*-request.json')) for p in directories)
    report = read(root / 'move/original-report.json')
    assert unpack(json.loads(view_bytes)) == report
    assert report['terminal']['status'] == 'completed' and report['terminal']['release']['verified']
    assert [e['id'] for e in raw if e['event'] == 'accepted'] == ['move-save']
    observations = [e for e in raw if e['event'] == 'observation']
    decoder = Decoder('live-control')
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as picture:
            assert (picture.width, picture.height, picture.mode, picture.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    rect = ET.parse(runtime / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    actual = {key: rect.get(key) for key in ('x', 'y', 'width', 'height', 'transform')}
    assert actual == raw[-1]['actual'] == {'x': '52', 'y': '50', 'width': '40', 'height': '30', 'transform': None}
    assert raw[-1]['success']
    result = {
        'audit_sha256': digest(Path(__file__).read_bytes()),
        'source_manifests_verified': True, 'full_events': len(raw), 'exact_frames': len(observations),
        'socket_exchanges': exchanges, 'pages': len(pages), 'additional_page_cli_calls': len(directories),
        'view_source_bytes': len(view_bytes), 'page_wire_bytes': sum(len(wire(p)) for p in pages),
        'capture_to_terminal_seconds': (report['terminal']['terminal_ns'] - observations[0]['capture_ns']) / 1e9,
        'capture_to_evaluation_seconds': (raw[-1]['known_ns'] - observations[0]['capture_ns']) / 1e9,
        'terminal_to_evaluation_seconds': (raw[-1]['known_ns'] - report['terminal']['terminal_ns']) / 1e9,
        'first_report_reply_to_last_page_cli_seconds': (read(directories[-1] / 'timing.json')['returned_ns'] - report['exchanges'][-1]['returned_ns']) / 1e9,
        'task_success': True, 'saved_rectangle': actual,
        'presentation': read(root / 'presentation.json'),
        'scope': 'One actual known-fixture episode; receipt-to-page interval includes orchestration/review/commentary. No causal latency, actual token, or human-speed claim. Old fixture provides no structured per-child cleanup audit.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
