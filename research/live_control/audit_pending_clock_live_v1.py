"""Audit actual pending-clock reader use and subsequent saved task result."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from received_history_v1 import assemble
from pointer_report_view_v1 import pack, unpack
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def main():
    cohort = HERE / 'results/pending-clock-live-01'
    root = cohort / 'runtime'
    for sources in (read(cohort / 'plan.json')['sources'], read(root / 'sources.json')):
        for name, digest in sources.items():
            assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == digest, name
    raw = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    segments = [{'request': read(root / 'initial-request.json'), 'reply': read(root / 'initial-batch.json')}]
    reports = {}
    for name in ('advance', 'stale-right', 'move-call'):
        report = read(root / name / 'report.json')
        view = read(root / name / 'view.json')
        assert pack(report) == view and unpack(view) == report
        reports[name] = report
        segments += report['exchanges']
    drain = read(root / 'drain/report.json')
    assert drain['state'] == 'own_clock_received_review_required' and len(drain['reads']) == 1
    assert 'command' not in drain['reads'][0]['request']
    assert drain['reads'][0]['request'] == read(root / 'drain/read-1-request.json')
    assert drain['reads'][0]['reply'] == read(root / 'drain/read-1-reply.json')
    assert drain['history'] == assemble(reports['stale-right']['exchanges'] + drain['reads'])
    assert reports['move-call']['source_image']['sequence'] == 2
    assert read(root / 'move-call/source-batch.json') == drain['history']['review_batch']
    assert drain['clock']['sequence'] == 2
    segments += drain['reads'] + [{'request': read(root / 'finish-request.json'), 'reply': read(root / 'finish-reply.json')}]
    covered = set()
    for segment in segments:
        a, b = segment['request']['after'], segment['reply']['cursor']
        assert segment['reply']['records'] == raw[a:b]
        assert b - a == len(segment['reply']['records'])
        covered.update(range(a, b))
    assert covered == set(range(len(raw)))
    assert reports['stale-right']['program_sent'] is False
    assert [e['id'] for e in raw if e['event'] == 'accepted'] == ['advance', 'move-save']
    assert all(e['status'] == 'completed' and e['release']['verified'] for e in raw if e['event'] == 'terminal')
    admitted = next(i for i, e in enumerate(raw) if e['event'] == 'accepted' and e['id'] == 'move-save')
    assert not any(e['event'] in ('input_admission', 'pointer_admission') for e in raw[:admitted])
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((root / f'{index:03d}.ait').read_bytes())
        with Image.open(root / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    image = read(root / 'drain/image.json')
    assert image['sequence'] == 2 and hashlib.sha256((root / image['relative_path']).read_bytes()).hexdigest() == image['sha256']
    evaluation = read(root / 'finish-reply.json')['records'][-1]
    rectangle = ET.parse(root / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    assert {k: rectangle.get(k) for k in evaluation['actual']} == evaluation['actual']
    assert evaluation['success'] and evaluation['actual'] == {'x': '52', 'y': '50', 'width': '40', 'height': '30', 'transform': None}
    timing = read(root / 'drain/timing.json')
    summary = {'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'exact_frames': len(observations), 'unique_records': len(raw), 'socket_exchanges': len(segments),
               'additional_read_only_exchanges': len(drain['reads']),
               'local_drain_and_report_persistence_ms': (timing['returned_ns'] - timing['started_ns']) / 1e6,
               'capture_to_evaluation_seconds': (evaluation['known_ns'] - observations[0]['capture_ns']) / 1e9,
               'saved_rectangle': evaluation['actual'], 'presentation': read(cohort / 'presentation.json'),
               'scope': 'One actual known-fixture episode with deliberate stale setup. Local timing excludes image presentation/model review; no paired speed, precision distance, or token claim.'}
    (cohort / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
