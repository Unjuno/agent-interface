"""Read-only archive consistency checks; never replay inputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = read(ROOT/'MANIFEST.json')
    for name, expected in manifest.items():
        assert digest(ROOT/name) == expected, name
    live = ROOT/'live'
    freeze = read(live/'FREEZE.json')
    for name, expected in freeze['sources'].items():
        assert digest(live/'source'/name) == expected, name
    assert digest(live/'owner.py') == freeze['owner_sha256']
    first = read(live/'action-2-metadata.json')
    lookup = read(live/'action-3-metadata.json')
    assert first['call_id'] == lookup['call_id']
    assert first['outcome_summary'] == lookup['outcome_summary']
    assert first['receipt']['source']['raw_report'] == lookup['receipt']['source']['raw_report']
    assert first['outcome_summary']['execution_status'] == 'completed'
    assert first['outcome_summary']['input_release_verified'] is True
    assert lookup['operation_invoked'] is False
    assert lookup['image_delivery'] == 'omitted_by_request'
    assert all(b['type'] != 'image' for b in read(live/'action-3-response.json')['content'])
    before = {r['path'].replace('\\', '/'): r['sha256'].lower()
              for r in read(live/'before-lookup-hashes.json')}
    after = {p.relative_to(live/'calls').as_posix(): digest(p)
             for p in (live/'calls').rglob('*') if p.is_file()}
    assert before == after
    assert len(after) == 6
    requests = [read(p) for p in (live/'calls').glob('*/request.json')]
    assert sorted(r['operation'] for r in requests) == ['dispatch', 'observe']
    assert read(live/'effect.json') == {'saved': True, 'text': 'receipt-72'}
    assert read(live/'primary-declaration.json')['primary_complete'] is True
    native = read(ROOT/'native/result.json')
    assert native['status'] == 'PASS'
    assert all(s['returncode'] == 0 for s in native['suites'])
    for suite in native['suites']:
        for log in suite['logs'].values():
            assert digest(ROOT/'native'/log['file']) == log['sha256']
    print(json.dumps({'status': 'PASS_ARCHIVE_CONSISTENCY',
                      'original_files': len(manifest), 'retained_call_files': len(after),
                      'source_revision': freeze['revision'],
                      'scope': 'saved evidence only; no GUI execution or independent adoption audit'}))


if __name__ == '__main__':
    main()
