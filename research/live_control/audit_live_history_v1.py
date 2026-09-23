"""Audit live fault injection separately from task correctness."""
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
    root = HERE / 'results/live-history-01'
    probe, runtime = root / 'probe', root / 'runtime'
    for sources in (read(probe / 'plan.json')['sources'], read(runtime / 'sources.json')):
        for name, digest in sources.items():
            assert hashlib.sha256((HERE.parent / name).read_bytes()).hexdigest() == digest, name
    raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
    segments = read(probe / 'segments.json')
    cursor = 0
    for segment in segments:
        request, reply = segment['request'], segment['reply']
        assert request['after'] == cursor
        assert reply['records'] == raw[cursor:reply['cursor']]
        cursor = reply['cursor']
    assert cursor == len(raw)
    assert assemble(segments)['review_batch']['records'] == raw
    for name in ('advance', 'stale-right', 'recover-observe'):
        report = read(probe / (name + '-report.json'))
        view = read(probe / (name + '-view.json'))
        assert pack(report) == view and unpack(view) == report
    stale = read(probe / 'stale-right-report.json')
    assert stale['program_sent'] is False and len(stale['exchanges']) == 1
    request, reply = (stale['exchanges'][0][k] for k in ('request', 'reply'))
    assert reply['records'][0]['command']['transport_request_id'] == request['request_id']
    assert reply['records'][-1]['sequence'] == 2 and stale['source_image']['sequence'] == 1
    assert stale['reason'] == 'clock sequence or timestamp mismatch; no new image authority'
    assert [e['id'] for e in raw if e['event'] == 'accepted'] == ['advance', 'recover-observe']
    assert not any(e['event'] in ('input_admission', 'pointer_admission', 'keys_held') for e in raw)
    assert all(e['operation'] == 'observe' for e in raw if e['event'] == 'step_started')
    assert all(e['status'] == 'completed' and e['release']['verified'] for e in raw if e['event'] == 'terminal')
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((runtime / f'{index:03d}.ait').read_bytes())
        with Image.open(runtime / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    before = read(probe / 'assembled-before-recovery.json')
    assert before == assemble(segments[:4])
    assert read(probe / 'recover-observe-source.json') == before['review_batch']
    evaluation = read(probe / 'finish.json')['records'][-1]
    assert evaluation['success'] is False  # Intentionally no rectangle movement.
    rectangle = ET.parse(runtime / 'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect')
    assert {k: rectangle.get(k) for k in evaluation['actual']} == evaluation['actual']
    assert rectangle.get('x') == '50' and rectangle.get('y') == '50'
    result = {'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_hashes_verified': True, 'exact_frames': len(observations),
              'full_prefix_records': len(raw), 'socket_exchanges': len(segments),
              'own_clock_sequence_mismatch': True, 'stale_input_submitted': False,
              'recorded_physical_inputs': 0, 'assembled_history_used_for_observe_recovery': True,
              'task_success': False, 'task_success_expected': False,
              'scope': 'Scripted live fault injection and observe-only recovery; no model speed, task success or token claim.'}
    (root / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
