import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import xml.etree.ElementTree as ET
from openpyxl import load_workbook

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[2]))
from runtime.cli_v1.receipt_references import expand_receipt

with tarfile.open(root / 'raw.tar.gz') as tar:
    members = {m.name: m for m in tar.getmembers()}
    manifest = json.loads((root / 'manifest.json').read_text())['files']
    assert len(members) == len(tar.getmembers()) and set(members) == set(manifest)
    def read(name):
        return tar.extractfile(members[name]).read()
    def data(name):
        return json.loads(read(name))
    for name, digest in manifest.items():
        assert hashlib.sha256(read(name)).hexdigest() == digest, name
    p = 'results-local/compact-primary-01/'
    sid = data(p + 'initial-metadata.json')['session']['session_id']
    refs = images = 0
    for label in ['initial'] + [f'action-{i}' for i in range(1, 16)]:
        row = data(p + label + '-metadata.json')
        assert row['session']['session_id'] == sid
        request = data(p + label + '-request.json')
        if request['tool'] in ('interface_observe', 'interface_dispatch'):
            assert request['arguments']['compact'] is True
            assert request['arguments']['report_refs'] is True
            assert row['receipt']['schema'] == 'agent-interface/receipt-view-v3-report-ref'
            expanded = expand_receipt(row['receipt'])
            assert expanded['source']['raw_report'] == row['receipt']['source']['raw_report']
            refs += 1
        blocks = [b for b in data(p + label + '-response.json')['content'] if b['type'] == 'image']
        if blocks:
            assert len(blocks) == 1
            assert base64.b64decode(blocks[0]['data']) == read(p + label + '.png')
            images += 1
    assert refs == 11 and images == 15
    close = data(p + 'action-15-metadata.json')
    assert close['status'] == 'closed' and close['release']['verified']
    assert close['release']['keys_down'] == close['release']['buttons_down'] == []
    book = load_workbook(io.BytesIO(read(p + 'saved.xlsx')), data_only=True)
    assert [book.active['A1'].value, book.active['A2'].value] == [548, 478]
    book.close()
    rect = ET.fromstring(read(p + 'saved.svg')).find('.//{http://www.w3.org/2000/svg}rect')
    assert [float(rect.get(k)) for k in ('x', 'y', 'width', 'height')] == [56, 50, 40, 30]
    assert rect.get('transform') is None
    assert data(p + 'fixture-cleanup.json')['session_close_returned']
    assert data(p + 'primary-review.json')['status'] == 'VISUALLY_COMPLETE_WITH_TEXT_RECOVERY'
    assert data(p + 'RESULT.json')['model_tokens'] is None
print('PASS', len(members), 'files; live compact receipts and final effects, with recovery retained')
