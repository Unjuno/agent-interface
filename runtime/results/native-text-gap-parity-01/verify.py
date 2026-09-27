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
assert cells['A1'] == '779' and cells['A2'] == '881'
programs = [json.loads(v)['ops'] for n,v in files.items() if '/program-guarded-' in n]
writes = [ops for ops in programs if any(op['op'] == 'text' for op in ops)]
assert len(writes) == 1
assert [op['timeout_ms'] for op in writes[0] if op['op'] == 'wait_update'] == [20,20,10,10,250]
assert ''.join(op['text'] for op in writes[0] if op['op'] == 'text') == '779881'
status = json.loads(files['action-4-metadata.json'])['allocation']
assert status['status'] == 'terminal' and status['returncode'] == 0
print('PASS: archive hashes, saved cells, compiled pacing and owner exit')
