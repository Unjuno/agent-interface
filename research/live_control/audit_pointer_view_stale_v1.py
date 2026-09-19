"""Audit overlapping received prefixes and explicit recovery in actual Inkscape use."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from pointer_report_view_v1 import pack, unpack
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    cohort = HERE / 'results/pointer-view-stale-01'
    root = cohort / 'runtime'
    for sources in (read(cohort / 'plan.json')['sources'], read(root / 'sources.json')):
        for name, digest in sources.items():
            assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == digest, name
    raw = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    pairs = [(read(root / 'initial-request.json'), read(root / 'initial-batch.json'))]
    reports = {}
    for name in ('advance-call', 'stale-call', 'move-call', 'corrected-call'):
        report = read(root / name / 'report.json')
        view = read(root / name / 'view.json')
        assert pack(report) == view
        assert json.dumps(unpack(view), sort_keys=True) == json.dumps(report, sort_keys=True)
        reports[name] = report
        for index, item in enumerate(report['exchanges'], 1):
            assert item['request'] == read(root / name / f'request-{index}.json')
            assert item['reply'] == read(root / name / f'reply-{index}.json')
            pairs.append((item['request'], item['reply']))
    pairs += [(read(root / a), read(root / b)) for a, b in (
        ('recovery-request.json', 'recovery-batch.json'), ('finish-request.json', 'finish-reply.json'))]
    covered = set()
    total = 0
    for request, reply in pairs:
        start, end = request['after'], reply['cursor']
        assert reply['records'] == raw[start:end]
        assert end - start == len(reply['records'])
        covered.update(range(start, end))
        total += len(reply['records'])
    assert covered == set(range(len(raw)))
    stale = reports['stale-call']
    assert stale['state'] == 'needs_reconciliation' and stale['program_sent'] is False
    assert stale['reason'] == 'own command echo required' and len(stale['exchanges']) == 1
    assert stale['exchanges'][0]['request']['command']['op'] == 'clock'
    assert 'continuation_batch' not in stale
    rejected = reports['move-call']
    assert rejected['state'] == 'needs_reconciliation' and rejected['program_sent'] is True
    assert rejected['last_reply']['status'] == 'unattributed_rejection'
    assert 'continuation_batch' not in rejected
    assert rejected['last_reply']['records'][-1]['reason'] == 'unsupported key'
    assert [e['id'] for e in raw if e['event'] == 'accepted'] == ['advance-observation', 'corrected-move-save']
    assert not any(e.get('id') in ('stale-right', 'move-save') and e['event'] in ('step_started', 'pointer_admission', 'accepted') for e in raw)
    first_input = next(i for i, e in enumerate(raw) if e['event'] in ('input_admission', 'pointer_admission'))
    corrected_admission = next(i for i, e in enumerate(raw) if e['event'] == 'accepted' and e['id'] == 'corrected-move-save')
    assert first_input > corrected_admission
    # Explicit reassembly must be exactly the received contiguous slice, including rejection.
    joined = read(root / 'reconciled-batch.json')
    assert joined['cursor'] == 16 and joined['records'] == raw[4:16]
    assert read(root / 'corrected-call/source-batch.json') == joined
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((root / f'{index:03d}.ait').read_bytes())
        with Image.open(root / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    evaluation = read(root / 'finish-reply.json')['records'][-1]
    rectangle = ET.parse(root / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    assert evaluation['success'] is True
    assert {k: rectangle.get(k) for k in ('x', 'y', 'width', 'height', 'transform')} == evaluation['actual']
    assert evaluation['actual'] == {'x': '52', 'y': '50', 'width': '40', 'height': '30', 'transform': None}
    assert all(e['status'] == 'completed' and e['release']['verified'] for e in raw if e['event'] == 'terminal')
    summary = {
        'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'unique_records': len(raw), 'received_records_including_overlap': total,
        'socket_exchanges': len(pairs), 'exact_frames': len(observations),
        'stale_attempt_sent_input_program': False,
        'malformed_attempt_admitted': False, 'explicit_corrected_attempt_completed': True,
        'saved_rectangle': evaluation['actual'],
        'capture_to_evaluation_seconds': (evaluation['known_ns'] - observations[0]['capture_ns']) / 1e9,
        'scope': 'Actual known-fixture recovery; stale historical clock boundary, not direct sequence mismatch. Legacy move-right contract, not precision distance. No timing/token comparison.',
    }
    (cohort / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
