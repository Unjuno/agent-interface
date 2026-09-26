"""Verify retained bytes without executing the archived runtime or harness."""
import base64
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET


def verify(root):
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    archive = root / 'evidence.tar.gz'
    description = json.loads((root / 'archive.json').read_text())
    assert sha(archive.read_bytes()) == description['sha256']
    manifest = json.loads((root / 'manifest.json').read_text())
    expected = {r['path']: r for r in manifest}
    assert len(expected) == len(manifest) == description['files'] == 73
    data = {}
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        assert len(members) == len(expected) and {m.name for m in members} == set(expected)
        for member in members:
            assert member.isfile() and not member.issym() and not member.islnk()
            raw = stream.extractfile(member).read()
            assert sha(raw) == expected[member.name]['sha256']
            assert len(raw) == expected[member.name]['bytes']
            data[member.name] = raw
    load = lambda name: json.loads(data[name])
    for name, want in load('evidence-sha256.json').items():
        assert sha(data[name]) == want
    assert sha(data['candidate/runtime.pyz']) == 'aa9024a5eea4384bdbba349b907f9f2a279ca2d041e50418a7820e778591aae0'
    assert load('candidate/manifest.json')['source_revision'] == '2dff80852292cc82fd5c23a449c8244bea94bc25'
    labels = ('initial', 'action-1', 'action-2', 'action-3')
    operations = []
    for label in labels:
        prefix = 'attempts/' + label + '/'
        request, report = load(prefix + 'request.json'), load(prefix + 'report.json')
        operations.append(request['operation'])
        response = load(label + '-stdout.json')
        assert {k: v for k, v in response.items() if k != 'image'} == load(label + '-metadata.json')
        assert base64.b64decode(response['image']['data'], validate=True) == data[label + '.png']
        source = response['receipt']['source']
        assert source['raw_report'] == report and source['sha256'] == sha(data[prefix + 'report.json'])
        assert response['retention']['request_persisted'] is True
        assert response['retention']['report_persisted'] is True
        assert response['retention']['replay_allowed'] is False
        assert load(label + '-timing.json')['exit_code'] == 0
        if request['operation'] == 'dispatch':
            assert request['arguments']['program'] == load(label + '-program.json')
            assert report['result']['status'] == 'completed'
            releases = report['result']['execution']['releases']
            assert releases and all(r['verified'] is True and r['keys_down'] == []
                                    and r['buttons_down'] == [] for r in releases)
    assert operations == ['observe', 'dispatch', 'dispatch', 'observe']
    assert len([n for n in data if n.startswith('attempts/') and n.endswith('/request.json')]) == 4
    ns = {'t': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
          'o': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
    rows = ET.fromstring(data['invoice.fods']).findall('.//t:table-row', ns)
    assert [''.join(c.itertext()).strip() for c in rows[0].findall('t:table-cell', ns)[:3]] == ['Quantity', 'Unit price', 'Total']
    cells = rows[1].findall('t:table-cell', ns)[:3]
    assert [c.get('{' + ns['o'] + '}value') for c in cells] == ['6', '23', '138']
    assert cells[2].get('{' + ns['t'] + '}formula') == 'of:=[.B2]*[.A2]'
    cleanup = load('cleanup.json')['tracked_processes']
    assert len(cleanup) == 3
    assert all(type(p['returncode']) is int and p['remaining_member_paths'] == [] for p in cleanup)
    return {'decision': 'PASS_RETAINED_CLI_RECORD_CONSISTENCY', 'files': len(data),
            'attempts': len(labels), 'saved_total': 138,
            'scope': 'Historical records only; no live process, power-loss or performance proof.'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent)))
