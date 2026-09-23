"""Offline retained-byte and saved-file audit; does not import the controller."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
run = root/'run'
def read(path):
    return json.loads(path.read_bytes())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
manifest = read(root/'manifest.json')
for name, expected in manifest.items():
    assert digest(root/name) == expected, name
links = 0
def images(value):
    global links
    if isinstance(value, dict):
        if isinstance(value.get('native'), dict) and 'artifact' in value['native']:
            native = value['native']
            artifact = native['artifact']
            path = run/'bridge/images'/Path(artifact['path']).name
            assert digest(path) == artifact['sha256']
            assert artifact['source_raw_sha256'] == native['sha256']
            assert value['capture_ns'] == native['capture_started_ns']
            links += 1
        for child in value.values():
            images(child)
    elif isinstance(value, list):
        for child in value:
            images(child)
for path in run.rglob('*.json'):
    images(read(path))
actions = read(run/'actions.json')
assert len(actions) == 3
emissions = []
for stage, action in enumerate(actions, 1):
    reply = read(run/f'reply-{stage}.json')
    request = read(run/f'request-{stage}.json')
    source = read(run/f'source-{stage}.json')
    assert reply['decision_sha256'] == digest(run/f'request-{stage}.json')
    assert reply['stage'] == stage
    assert request['source_sequence'] == source['sequence']
    assert action['result']['status'] == 'completed'
    releases = action['result']['execution']['releases']
    assert releases and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in releases)
    emissions.append(action['result']['execution']['program_emissions'])
with zipfile.ZipFile(run/'sheet.xlsx') as workbook:
    sheet = ET.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
cells = {c.attrib['r']:c.findtext('s:v', namespaces=ns) for c in sheet.findall('.//s:c', ns)}
assert cells['A1'] == '190' and cells['A2'] == '676' and cells.get('B1') is None
svg = ET.parse(run/'shape.svg').getroot()
rect = next(r for r in svg.iter() if r.tag.endswith('}rect'))
assert {k:rect.get(k) for k in ['x','y','width','height','transform']} == {
    'x':'86','y':'50','width':'40','height':'30','transform':None}
final = read(run/'reply-3.json')
assert final['evaluation']['success'] is True
assert all(v['success'] is True for v in final['evaluation']['applications'].values())
assert final['cleanup']['status'] == 'completed' and final['cleanup']['tracked_processes_terminal']
assert read(root/'provenance.json')['owner_exit_code'] == 0
print(json.dumps({'status':'PASS_SCOPED','manifest_files':len(manifest),
                  'image_links':links,'program_emissions':emissions,
                  'feedback_statuses':[a['feedback']['status'] for a in actions],
                  'task_scores':[True,True], 'normal_app_shutdown_proven':False}))
