"""Audit first actual use of reversible caller stdout plus images."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image
from session_v4 import Decoder
from pointer_report_view_v1 import pack, unpack

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'openttd_task'))
from guarded_score import score


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cohort = HERE / 'results/pointer-view-live-01'
    root = cohort / 'runtime'
    for manifest in (cohort / 'plan.json', root / 'manifest.json'):
        for path, digest in read(manifest)['sources'].items():
            assert sha(HERE.parent / path) == digest, path
    raw = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    initial = read(root / 'initial-batch.json')
    exchanges = [(read(root / 'initial-request.json'), initial)]
    calls = []
    for name in ('open-call', 'road-call'):
        report = read(root / name / 'report.json')
        view = read(root / name / 'view.json')
        assert pack(report) == view
        assert json.dumps(unpack(view), sort_keys=True) == json.dumps(report, sort_keys=True)
        assert report['state'] == 'terminal' and report['terminal']['status'] == 'completed'
        assert len(report['exchanges']) == 2
        for index, item in enumerate(report['exchanges'], 1):
            assert item['request'] == read(root / name / f'request-{index}.json')
            assert item['reply'] == read(root / name / f'reply-{index}.json')
            exchanges.append((item['request'], item['reply']))
        selected = report['image']
        assert sha(root / selected['relative_path']) == selected['sha256']
        records = report['last_reply']['records']
        accepted = next(e for e in records if e['event'] == 'accepted')
        observed = next(e for e in records if e['event'] == 'observation')
        calls.append({
            'call': name,
            'original_json_bytes': len(json.dumps(report, ensure_ascii=False).encode()),
            'view_json_bytes': len(json.dumps(view, ensure_ascii=False).encode()),
            'local_two_exchange_ms': (report['exchanges'][-1]['returned_ns'] - report['exchanges'][0]['started_ns']) / 1e6,
            'admission_to_first_capture_ms': (observed['capture_ns'] - accepted['accepted_ns']) / 1e6,
            'admission_to_first_emission_ms': (observed['emitted_ns'] - accepted['accepted_ns']) / 1e6,
            'image_sequence_displayed_by_orchestrator': selected['sequence'],
        })
    exchanges.append((read(root / 'finish-request.json'), read(root / 'finish-reply.json')))
    cursor = 0
    received = []
    for request, reply in exchanges:
        assert request['after'] == cursor
        cursor += len(reply['records'])
        assert reply['cursor'] == cursor
        received += reply['records']
    assert received == raw
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for index, event in enumerate(observations, 1):
        assert event['sequence'] == index
        frame = decoder.accept((root / f'{index:03d}.ait').read_bytes())
        with Image.open(root / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    admissions = [e for e in raw if e['event'] == 'accepted']
    terminals = [e for e in raw if e['event'] == 'terminal']
    assert [e['id'] for e in admissions] == ['open-toolbar', 'build-road']
    assert [e['id'] for e in terminals] == ['open-toolbar', 'build-road']
    assert all(e['status'] == 'completed' and e['release']['verified'] for e in terminals)
    evidence = read(root / 'evaluation.json')
    verdict = score(evidence['observation'], evidence['baseline'])
    assert verdict['success']
    cleanup = read(root / 'cleanup.json')
    assert cleanup['all_owned_processes_exited'] and cleanup['save_unchanged']
    summary = {
        'audit_sha256': sha(Path(__file__)), 'source_manifests_verified': True,
        'exact_frames': len(observations), 'full_prefix_records': len(raw),
        'socket_exchanges': len(exchanges), 'calls': calls,
        'capture_to_last_terminal_seconds': (terminals[-1]['terminal_ns'] - observations[0]['capture_ns']) / 1e9,
        'capture_to_evaluation_seconds': (raw[-1]['emitted_ns'] - observations[0]['capture_ns']) / 1e9,
        'score': verdict, 'cleanup': cleanup,
        'presentation': read(cohort / 'presentation.json'),
        'scope': 'Known fixture, one actual assistant episode. Runtime latency is not model receipt latency or first useful feedback; no paired speed/token qualification.',
    }
    (cohort / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
