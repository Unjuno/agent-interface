"""Verify retained files and outcomes; does not infer UI speed or causal benefit."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET
from openpyxl import load_workbook

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
    cases = [('two-app-primary-01', [150, 625], 50),
             ('explicit-window-activation-primary-01', [134, 317], 56),
             ('explicit-window-activation-primary-02', [108, 161], 56)]
    for case, expected, x in cases:
        p = 'results-local/' + case + '/'
        book = load_workbook(io.BytesIO(read(p + 'saved.xlsx')), data_only=True)
        assert [book.active['A1'].value, book.active['A2'].value] == expected
        book.close()
        rect = ET.fromstring(read(p + 'saved.svg')).find('.//{http://www.w3.org/2000/svg}rect')
        assert [float(rect.get(k)) for k in ('x', 'y', 'width', 'height')] == [x, 50, 40, 30]
        assert rect.get('transform') is None
        assert data(p + 'fixture-cleanup.json')['session_close_returned']
    p = 'results-local/explicit-window-activation-primary-02/'
    sid = data(p + 'initial-metadata.json')['session']['session_id']
    images = 0
    for label in ['initial'] + [f'action-{n}' for n in range(1, 15)]:
        assert data(p + label + '-metadata.json')['session']['session_id'] == sid
        blocks = [b for b in data(p + label + '-response.json')['content'] if b['type'] == 'image']
        if blocks:
            assert len(blocks) == 1
            assert base64.b64decode(blocks[0]['data']) == read(p + label + '.png')
            images += 1
    assert images == 14
    for n in (1, 4, 7, 8, 9, 10, 11, 12, 13):
        outcome = data(p + f'action-{n}-metadata.json')['outcome_summary']
        assert outcome['execution_status'] == 'completed' and outcome['input_release_verified']
    for n, target in ((7, 'inkscape'), (11, 'calc')):
        op = data(p + f'action-{n}-request.json')['arguments']['program']['ops'][0]
        assert op == {'op': 'activate', 'target': target, 'timeout_ms': 500}
    closed = data(p + 'action-14-metadata.json')
    assert closed['status'] == 'closed' and closed['release']['verified']
    assert closed['release']['keys_down'] == closed['release']['buttons_down'] == []
    assert data(p + 'evaluation.json')['success']
    assert data(p + 'inkscape-evaluation.json')['success']
    failed = data('results-local/explicit-window-activation-primary-01/action-18-response.json')
    assert failed['isError'] and 'Unknown tool' in failed['content'][0]['text']
    assert data('results-local/explicit-window-activation-check-02/result.json')['status'] == 'PASS'
print('PASS:', len(members), 'retained files; baseline failure, driver failure, and staged success preserved')
