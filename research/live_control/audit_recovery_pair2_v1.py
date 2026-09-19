"""Audit both arms of registered pair 2; exact model performance remains unqualified."""
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


def audit(arm):
    root = HERE / 'results/recovery-pair2-01' / arm
    runtime = root / 'runtime'
    metadata = read(root / 'initial/execution.json')
    assert metadata['pair'] == 2 and metadata['arm'] == arm and metadata['seed'] == 202
    assert metadata['runner_sha256'] == hashlib.sha256((HERE / 'recovery_pair2_v1.py').read_bytes()).hexdigest()
    plan = read(HERE / 'recovery_comparison_plan_v1.json')
    assert metadata['plan_sha256'] == hashlib.sha256((HERE / 'recovery_comparison_plan_v1.json').read_bytes()).hexdigest()
    for sources in (plan['sources'], read(runtime / 'sources.json')):
        for name, digest in sources.items():
            assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == digest
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    segments = []
    for stage in ('initial', 'prepare', 'move', 'finish', *(['recover1'] if arm == 'B' else ['recover1', 'recover2', 'recover3', 'recover4'])):
        for q in sorted((root / stage).glob('query-*-request.json')):
            segments.append({'request': read(q), 'reply': read(q.with_name(q.name.replace('-request', '-reply')))})
    if arm == 'B':
        drain = read(root / 'recover1/drain-report.json')
    else:
        reads = [read(root / ('recover' + str(i)) / 'new-slices.json')[0] for i in range(1, 5)]
        drain = {'state': 'own_clock_received_review_required', 'reads': reads, 'history': read(root / 'recover4/history.json')}
        for i in range(1, 5):
            prior = read(root / 'prepare/stale-right-report.json')['exchanges'] + reads[:i]
            assert read(root / ('recover' + str(i)) / 'history.json') == assemble(prior)
    assert drain['state'] == 'own_clock_received_review_required' and len(drain['reads']) == 4
    assert all('command' not in item['request'] for item in drain['reads'])
    if arm == 'B':
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
              'pair': 2, 'arm': arm, 'recovery_reads': 4, 'additional_historical_clocks': 3,
              'own_clock_final_read': True, 'recovery_outer_calls_reported': read(root / 'presentation.json')['recovery_outer_calls'],
              'socket_exchanges': len(segments), 'unique_records': len(raw), 'exact_frames': len(observations),
              'task_success': True,
              'capture_to_evaluation_seconds': (evaluation['known_ns'] - observations[0]['capture_ns']) / 1e9,
              'paired_effect': None, 'model_performance_qualified': False,
              'next': 'Pair 3 OpenTTD B then A; do not rerun pair 2.'}
    (root / 'paired-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    rows = {arm: audit(arm) for arm in ('B', 'A')}
    root = HERE / 'results/recovery-pair2-01'
    assert read(root / 'A/move/move-save-steps.json') == read(root / 'B/move/move-save-steps.json')
    assert read(root / 'A/runtime/sources.json') == read(root / 'B/runtime/sources.json')
    assert (root / 'A/runtime/001.png').read_bytes() == (root / 'B/runtime/001.png').read_bytes()
    assert rows['A']['recovery_outer_calls_reported'] == 4 and rows['B']['recovery_outer_calls_reported'] == 1
    result = {'arms': rows, 'recovery_calls_B_minus_A': -3, 'recovery_socket_reads_B_minus_A': 0,
              'capture_to_evaluation_seconds_B_minus_A': rows['B']['capture_to_evaluation_seconds'] - rows['A']['capture_to_evaluation_seconds'],
              'model_performance_qualified': False, 'reason': 'model identity/configuration and receipt timestamps unavailable',
              'scheduled_episodes_completed': 4, 'scheduled_episodes_remaining': 4,
              'scope': 'One exploratory paired task. Separate model calls observed in conversation; no generalized latency or token claim.'}
    (root / 'pair-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
