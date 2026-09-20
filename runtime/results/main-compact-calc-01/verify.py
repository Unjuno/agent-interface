"""Read-only audit of this retained allocation; never executes archived code."""
import base64
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET


def verify(root):
    digest = lambda data: hashlib.sha256(data).hexdigest()
    archive = root / 'evidence.tar.gz'
    metadata = json.loads((root / 'archive.json').read_text())
    assert digest(archive.read_bytes()) == metadata['sha256'], 'archive digest'
    manifest = json.loads((root / 'manifest.json').read_text())
    expected = {r['path']: r for r in manifest}
    assert len(expected) == len(manifest) == metadata['files'] == 54
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        assert len(members) == len(expected)
        assert {m.name for m in members} == set(expected)
        data = {}
        for member in members:
            assert member.isfile() and not member.issym() and not member.islnk()
            raw = stream.extractfile(member).read()
            row = expected[member.name]
            assert len(raw) == row['bytes'] and digest(raw) == row['sha256'], member.name
            data[member.name] = raw
    load = lambda name: json.loads(data[name])
    for name, sha in load('evidence-sha256.json').items():
        # Original local manifest was produced on Windows; tar names use '/'.
        assert digest(data[name.replace('\\', '/')]) == sha, name
    assert digest(data['runtime.pyz']) == load('manifest.json')['sha256']
    assert load('manifest.json')['source_revision'] == 'b732fa5c3d4c828ea50f81c36522a61e7803e473'
    calls = []
    for label, tool in (('initial', 'interface_observe'), ('action-1', 'interface_dispatch'),
                        ('action-2', 'interface_dispatch'), ('action-3', 'interface_observe')):
        request = load(label + '-request.json')
        assert request['tool'] == tool
        assert request['arguments']['compact'] is True
        assert request['arguments']['report_refs'] is True
        reply = load(label + '-reply.json')
        blocks = reply['content']
        texts = [b['text'] for b in blocks if b['type'] == 'text']
        images = [b for b in blocks if b['type'] == 'image']
        assert len(texts) == len(images) == 1
        assert base64.b64decode(images[0]['data'], validate=True) == data[label + '.png']
        view = json.loads(texts[0])
        assert view == load(label + '-metadata.json')
        receipt = view['receipt']
        assert receipt['schema'] == 'agent-interface/receipt-view-v3-report-ref'
        assert receipt['report'] == {'report_ref': '/source/raw_report'}
        assert receipt['report_reference'] == '/source/raw_report'
        call = view['call_id']; calls.append(call)
        original = data['calls/' + call + '/report.json']
        assert digest(original) == receipt['source']['sha256']
        assert json.loads(original) == receipt['source']['raw_report']
        if tool == 'interface_dispatch':
            result = json.loads(original)['result']
            assert result['status'] == 'completed'
            releases = result['execution']['releases']
            assert releases and all(r['verified'] is True and r['keys_down'] == []
                                    and r['buttons_down'] == [] for r in releases)
    assert len(set(calls)) == 4
    assert len([name for name in data if name.startswith('calls/') and name.endswith('/request.json')]) == 4
    ns = {'t': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
          'o': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
    rows = ET.fromstring(data['invoice.fods']).findall('.//t:table-row', ns)
    assert [''.join(c.itertext()).strip() for c in rows[0].findall('t:table-cell', ns)[:3]] == ['Quantity', 'Unit price', 'Total']
    cells = rows[1].findall('t:table-cell', ns)[:3]
    assert [c.get('{' + ns['o'] + '}value') for c in cells] == ['8', '17', '136']
    assert cells[2].get('{' + ns['t'] + '}formula') == 'of:=[.B2]*[.A2]'
    cleanup = load('cleanup.json')
    assert len(cleanup['tracked_processes']) == 3
    assert all(type(p['returncode']) is int and p['remaining_member_paths'] == []
               for p in cleanup['tracked_processes'])
    return {'decision': 'PASS_RETAINED_RECORD_CONSISTENCY', 'files': len(data),
            'calls': len(calls), 'saved_total': 136,
            'scope': 'Historical bytes/records only; no independent live cleanup or performance proof.'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent)))
