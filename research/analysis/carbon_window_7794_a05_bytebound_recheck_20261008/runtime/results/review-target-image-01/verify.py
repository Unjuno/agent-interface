from pathlib import Path
import base64
import hashlib
import json
import tarfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'manifest.json').read_text())
with tarfile.open(root / 'raw.tar.gz', 'r:gz') as tar:
    members = {m.name: m for m in tar.getmembers()}
    assert len(members) == len(tar.getmembers())
    assert set(members) == set(manifest['files'])
    def read(name):
        return tar.extractfile(members[name]).read()
    def data(name):
        return json.loads(read(name))
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(read(name)).hexdigest() == digest, name
    p = 'results-local/review-target-image-primary-01/'
    def rectangle(name):
        rows = ET.fromstring(read(p + name)).findall('{http://www.w3.org/2000/svg}rect')
        assert len(rows) == 1 and rows[0].get('transform') is None
        return [float(rows[0].get(k)) for k in ('x', 'y', 'width', 'height')]
    assert rectangle('original.svg') == [50, 50, 40, 30]
    assert rectangle('saved-copy.svg') == [56, 50, 40, 30]
    assert data(p + 'evaluation.json')['success']
    sid = data(p + 'initial-metadata.json')['session']['session_id']
    count = 0
    for label in ['initial'] + [f'action-{n}' for n in range(1, 9)]:
        assert data(p + label + '-metadata.json')['session']['session_id'] == sid
        images = [x for x in data(p + label + '-response.json')['content'] if x['type'] == 'image']
        if images:
            assert len(images) == 1
            assert base64.b64decode(images[0]['data']) == read(p + label + '.png')
            count += 1
    assert count == 8
    row = data(p + 'action-3-metadata.json')
    assert row['status'] == 'target_reviewed' and row['binding_revision'] == 2
    assert row['capture_consistency'] == 'matched'
    assert row['observation_report']['status'] == 'returned'
    assert not row['input_dispatched'] and not row['authority_granted']
    assert data(p + 'action-4-request.json')['tool'] == 'interface_dispatch'
    for n in (1, 4, 5, 6):
        result = data(p + f'action-{n}-metadata.json')['outcome_summary']
        assert result['execution_status'] == 'completed' and result['input_release_verified']
    closed = data(p + 'action-8-metadata.json')
    assert closed['status'] == 'closed' and closed['release']['verified']
    assert closed['release']['keys_down'] == closed['release']['buttons_down'] == []
    assert data(p + 'fixture-cleanup.json')['session_close_returned']
    assert data('results-local/review-target-image-check-02/result.json')['status'] == 'PASS'
print('PASS', len(members), 'files; saved SVG and post-selection image verified; no performance inference')
