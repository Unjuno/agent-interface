import hashlib, io, json, tarfile, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
root = Path(__file__).resolve().parent
with tarfile.open(root / 'raw.tar.gz') as archive:
    files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
manifest = json.loads((root / 'manifest.json').read_text())
assert set(files) == set(manifest)
assert all(hashlib.sha256(files[n]).hexdigest() == h for n,h in manifest.items())
def read(n):
    return json.loads(files[n])
with zipfile.ZipFile(io.BytesIO(files['allocation/run/sheet.xlsx'])) as book:
    sheet = ET.fromstring(book.read('xl/worksheets/sheet1.xml'))
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
cells = {c.attrib['r']: c.find('s:v', ns).text for c in sheet.findall('.//s:c', ns) if c.find('s:v', ns) is not None}
assert cells['A1'] == '779' and cells['A2'] == '881'
decisions = [read(f'decision-{i}.json') for i in range(1,6)]
assert [d['arguments']['decision'].get('interaction') for d in decisions] == ['keyboard','observe','click','observe',None]
assert decisions[-1]['arguments']['decision']['finish'] is True
programs = [json.loads(v)['ops'] for n,v in files.items() if '/program-guarded-' in n]
assert len(programs) == 2
assert sorted(op['timeout_ms'] for ops in programs for op in ops if op['op'] == 'wait_update') == [10,10,20,20]
assert read('action-5-metadata.json')['outcome_summary']['evaluation_success'] is True
assert 'action-6-response.json' not in files
assert read('summary.json')['owner_exit_code'] is None
print('PASS: retained bytes, saved cells, two input programs, two read-only observations, no 250ms waits.')
print('Limits: transient-image interpretation and client exit are primary/tool observations, not inferred by this verifier.')
