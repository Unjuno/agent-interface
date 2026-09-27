import hashlib, io, json, tarfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
root = Path(__file__).resolve().parent
with tarfile.open(root / 'raw.tar.gz') as archive:
    files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
manifest = json.loads((root / 'manifest.json').read_text())
assert set(files) == set(manifest)
assert all(hashlib.sha256(files[n]).hexdigest() == h for n, h in manifest.items())
with zipfile.ZipFile(io.BytesIO(files['allocation/run/sheet.xlsx'])) as book:
    sheet = ET.fromstring(book.read('xl/worksheets/sheet1.xml'))
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
cells = {c.attrib['r']: c.find('s:v', ns).text for c in sheet.findall('.//s:c', ns) if c.find('s:v', ns) is not None}
assert cells['A1'] == '341' and cells['A2'] == '595'

reports = [json.loads(v) for n,v in files.items() if '/public-dispatch-guarded-' in n]
assert len(reports) == 2
for r in reports:
    assert r['schema'] == 'agent-interface/runtime-dispatch-result-v1'
    assert r['status'] == 'returned' and r['result']['status'] == 'completed'
    releases = r['result']['execution']['releases']
    assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
status = json.loads(files['action-4-metadata.json'])['allocation']
assert status['status'] == 'terminal' and status['returncode'] == 0

captures = [json.loads(v) for n,v in files.items() if '/public-observation-' in n]
observations = [json.loads(v) for n,v in files.items() if '/bridge/observation-' in n]
assert len(captures) == len(observations) == 10
assert len({r['observation_id'] for r in captures}) == 10
for r in captures:
    assert r['schema'] == 'agent-interface/runtime-observation-v1'
    assert r['status'] == 'returned'
    assert r['input_dispatched'] is False and r['side_effect_authority'] is False
    native = r['observation']
    assert sum(o['native'] == native for o in observations) == 1
assert json.loads(files['action-3-metadata.json'])['outcome_summary']['evaluation_success'] is True
print('PASS: hashes, saved cells, capture correspondence, releases and owner exit')
