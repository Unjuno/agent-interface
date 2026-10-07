"""Audit both failed drag task episodes; transport success is not task success."""
import json
from pathlib import Path
from PIL import Image
from decision_receipt_v3 import build
from report_pages_v2 import digest
from score_drag_v1 import score
from session_v4 import Decoder

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    rows = []
    for name in ('drag-live-01', 'drag-live-02'):
        root = HERE / 'results' / name
        runtime = root / 'runtime'
        for filename, sha in read(root / 'initial/plan.json')['sources'].items():
            assert digest((HERE / filename).read_bytes()) == sha
        for filename, sha in read(runtime / 'sources.json').items():
            assert digest((HERE.parent / filename).read_bytes()) == sha
        raw = [json.loads(line) for line in (runtime / 'events.jsonl').read_text().splitlines()]
        covered = set()
        exchanges = 0
        for stage in ('initial', 'select', 'drag', 'finish'):
            for path in sorted((root / stage).glob('query-*-request.json')):
                q = read(path)
                reply = read(path.with_name(path.name.replace('-request', '-reply')))
                a, b = q['after'], reply['cursor']
                assert reply['status'] == 'boundary' and reply['records'] == raw[a:b]
                assert b - a == len(reply['records']) and not covered.intersection(range(a, b))
                covered.update(range(a, b))
                exchanges += 1
        assert covered == set(range(len(raw)))
        for stage in ('select', 'drag'):
            receipt = read(root / stage / 'receipt.json')
            assert build((root / stage / 'report.json').read_bytes()) == receipt
            assert receipt['program_binding']['terminal']['status'] == 'completed'
            assert not receipt['detail_review_required']
        observations = [e for e in raw if e['event'] == 'observation']
        decoder = Decoder('live-control')
        for i, event in enumerate(observations, 1):
            assert event['sequence'] == i
            frame = decoder.accept((runtime / f'{i:03d}.ait').read_bytes())
            with Image.open(runtime / Path(event['image']).name) as picture:
                assert (picture.width, picture.height, picture.mode, picture.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
        strict = read(root / 'strict-score.json')
        assert strict['scorer_sha256'] == digest((HERE / 'score_drag_v1.py').read_bytes())
        assert strict['svg_sha256'] == digest((runtime / 'shape.svg').read_bytes())
        recomputed = score(runtime / 'shape.svg')
        assert all(strict[k] == v for k, v in recomputed.items())
        assert strict['success'] is False and raw[-1]['success'] is True
        assert all(e['release']['verified'] for e in raw if e['event'] == 'terminal')
        rows.append({'episode': name, 'task_success': strict['success'], 'legacy_score_success': raw[-1]['success'],
                     'actual': strict['actual'], 'events': len(raw), 'exact_frames': len(observations),
                     'socket_exchanges': exchanges, 'initial_png': digest((runtime / '001.png').read_bytes()),
                     'selected_png': read(root / 'select/receipt.json')['image']['sha256'],
                     'svg_sha256': strict['svg_sha256'],
                     'capture_to_evaluation_seconds': (raw[-1]['known_ns'] - observations[0]['capture_ns']) / 1e9})
    assert rows[0]['initial_png'] == rows[1]['initial_png']
    assert rows[0]['selected_png'] == rows[1]['selected_png']
    result = {'audit_passed': True, 'audit_sha256': digest(Path(__file__).read_bytes()), 'rows': rows,
              'decision': 'both fail declared displacement; endpoint dwell variant not adopted',
              'limits': 'Exploratory sequential self-use, not randomized performance study. First scorer coded after execution using predeclared numeric target; second scorer pinned before execution.'}
    target = HERE / 'results/drag-live-02/paired-audit.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
