"""Audit first arm of registered pair 2; no paired effect computed."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from session_v4 import Decoder
from received_history_v1 import assemble

HERE = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def main():
    root = HERE / 'results/recovery-pair2-01/B'
    runtime = root / 'runtime'
    metadata = read(root / 'initial/execution.json')
    assert metadata['pair'] == 2 and metadata['arm'] == 'B' and metadata['seed'] == 202
    assert metadata['runner_sha256'] == hashlib.sha256((HERE / 'recovery_pair2_v1.py').read_bytes()).hexdigest()
    plan = read(HERE / 'recovery_comparison_plan_v1.json')
    assert metadata['plan_sha256'] == hashlib.sha256((HERE / 'recovery_comparison_plan_v1.json').read_bytes()).hexdigest()
    for sources in (plan['sources'], read(runtime / 'sources.json')):
        for name, digest in sources.items():
            assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == digest
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    segments = []
    for stage in ('initial', 'prepare', 'recover1', 'move', 'finish'):
        for q in sorted((root / stage).glob('query-*-request.json')):
            segments.append({'request': read(q), 'reply': read(q.with_name(q.name.replace('-request', '-reply')))})
    drain = read(root / 'recover1/drain-report.json')
    assert drain['state'] == 'own_clock_received_review_required' and len(drain['reads']) == 4
    assert all('command' not in item['request'] for item in drain['reads'])
    segments += drain['reads']
    covered = set()
    for item in segments:
        a, b = item['request']['after'], item['reply']['cursor']
        assert item['reply']['records'] == raw[a:b] and b - a == len(item['reply']['records'])
        covered.update(range(a, b))
    assert covered == set(range(len(raw)))
    stale = read(root / 'prepare/stale-right-report.json')
    assert stale['program_sent'] is False
    assert drain['history'] == assemble(stale['exchanges'] + drain['reads'])
    assert read(root / 'move/move-save-source.json') == drain['history']['review_batch']
    queued = read(root / 'prepare/queued-clocks.json')
    for item, historical in zip(drain['reads'][:3], queued):
        assert item['reply']['records'][-2:] == historical['records']
    own = stale['exchanges'][0]['request']['request_id']
    assert drain['reads'][-1]['reply']['records'][-2]['command']['transport_request_id'] == own
    assert [e['id'] for e in raw if e['event'] == 'accepted'] == ['advance', 'move-save']
    assert all(e['status'] == 'completed' and e['release']['verified'] for e in raw if e['event'] == 'terminal')
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    evaluation = raw[-1]
    rect = ET.parse(runtime / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    assert evaluation['success'] and {k: rect.get(k) for k in evaluation['actual']} == evaluation['actual']
    assert evaluation['actual'] == {'x': '52', 'y': '50', 'width': '40', 'height': '30', 'transform': None}
    result = {'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'pair': 2, 'arm': 'B', 'recovery_reads': 4, 'additional_historical_clocks': 3,
              'own_clock_final_read': True, 'recovery_outer_calls_reported': 1,
              'socket_exchanges': len(segments), 'unique_records': len(raw), 'exact_frames': len(observations),
              'task_success': True,
              'capture_to_evaluation_seconds': (evaluation['known_ns'] - observations[0]['capture_ns']) / 1e9,
              'paired_effect': None, 'model_performance_qualified': False,
              'next': 'Pair 2 A with unchanged runner and same setup; do not rerun B.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
