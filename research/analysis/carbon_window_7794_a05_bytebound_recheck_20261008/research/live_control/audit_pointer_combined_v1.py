"""Audit actual combined-display episode and offline reversible view.

Model presentation failure is recorded from the conversation, not inferred
from runtime logs. This audit cannot verify model receipt times or token costs.
"""
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


def main():
    root = HERE / 'results/pointer-combined-openttd-01'
    for path, digest in read(root / 'manifest.json')['sources'].items():
        assert hashlib.sha256((HERE.parent / path).read_bytes()).hexdigest() == digest, path
    raw = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    batches = [read(root / 'initial-batch.json')]
    sizes = []
    for name in ('open-call', 'road-call'):
        report = read(root / name / 'report.json')
        assert report['state'] == 'terminal'
        batches += [item['reply'] for item in report['exchanges']]
        view = pack(report)
        assert json.dumps(unpack(view), sort_keys=True) == json.dumps(report, sort_keys=True)
        assert set(view['references']) == {'last_reply', 'continuation_batch', 'terminal'}
        (root / name / 'view.json').write_text(json.dumps(view, indent=2) + '\n')
        size = lambda value: len(json.dumps(value, ensure_ascii=False).encode())
        sizes.append({'call': name, 'original_json_bytes': size(report), 'view_json_bytes': size(view)})
        selected = report['image']
        assert hashlib.sha256((root / selected['relative_path']).read_bytes()).hexdigest() == selected['sha256']
    batches.append(read(root / 'finish-reply.json'))
    cursor = 0
    received = []
    for batch in batches:
        cursor += len(batch['records'])
        assert cursor == batch['cursor']
        received += batch['records']
    assert received == raw
    decoder = Decoder('live-control')
    observations = [e for e in raw if e['event'] == 'observation']
    for sequence, event in enumerate(observations, 1):
        assert event['sequence'] == sequence
        frame = decoder.accept((root / f'{sequence:03d}.ait').read_bytes())
        with Image.open(root / Path(event['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    terminals = [e for e in raw if e['event'] == 'terminal']
    assert len(terminals) == 2
    assert all(e['status'] == 'completed' and e['release']['verified'] is True for e in terminals)
    evidence = read(root / 'evaluation.json')
    result = score(evidence['observation'], evidence['baseline'])
    assert result['success'] is True
    cleanup = read(root / 'cleanup.json')
    assert cleanup['all_owned_processes_exited'] and cleanup['save_unchanged']
    # A differing receipt, rejected state or unknown diagnostic must survive.
    cases = [
        {'state': 'needs_reconciliation', 'reason': 'transport timeout', 'exchanges': []},
        {'exchanges': [{'reply': {'records': [1]}}], 'last_reply': {'records': [True]}, 'diagnostic': {'unexpected': [1, 2]}},
        {'exchanges': [{'reply': {'records': []}}], 'terminal': {'status': 'failed'}},
    ]
    for case in cases:
        assert json.dumps(unpack(pack(case)), sort_keys=True) == json.dumps(case, sort_keys=True)
        assert not pack(case)['references']
    summary = {
        'exact_frames': len(observations), 'full_prefix_records': len(raw),
        'independent_score': result, 'cleanup': cleanup, 'presentation_bytes': sizes,
        'offline_negative_cases': len(cases),
        'capture_to_last_terminal_seconds': (terminals[-1]['terminal_ns'] - observations[0]['capture_ns']) / 1e9,
        'capture_to_evaluation_seconds': (raw[-1]['emitted_ns'] - observations[0]['capture_ns']) / 1e9,
        'presentation_failure': 'Second full report output was truncated in conversation; assistant inspected saved image in a later tool call without resending input.',
        'scope': 'Known-fixture assistant use; offline reversible presentation only. No paired speed, token, cost, or model receipt measurements.',
        'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'view_source_sha256': hashlib.sha256((HERE / 'pointer_report_view_v1.py').read_bytes()).hexdigest(),
    }
    (root / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
