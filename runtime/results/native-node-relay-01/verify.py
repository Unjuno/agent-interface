"""Read retained bytes only; no extraction, archived-code execution or GUI rerun."""
import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
root=Path(__file__).parent

def require(ok,message):
    if not ok:raise ValueError(message)

with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members),'regular files only')
    require(len(members)==len({m.name for m in members}),'unique paths')
    files={m.name:archive.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(files)==set(manifest),'complete inventory')
for name,digest in manifest.items():require(hashlib.sha256(files[name]).hexdigest()==digest,name)
def read(name):return json.loads(files[name].decode('utf-8-sig'))
def reply(case,id):
    row=read(case+f'-evidence/reply-{id}.json')
    require(row['status']=='returned' and not row['result']['isError'],'RPC returned')
    return row,json.loads(row['result']['content'][0]['text'])
bad='native-node-relay-01'
require('TimeoutError: window sheet.xlsx' in files[bad+'/run/error.txt'].decode(),'initial failure retained')
require(not any(n.startswith(bad+'/run/request-') for n in files),'failed startup had no input')
properties=read('native-startup-diagnostic-03/title-properties.json')
require('N/A' in properties['wmctrl_utf8'],'wmctrl failure retained')
require(any('WM_NAME(COMPOUND_TEXT)' in v and '_NET_WM_VISIBLE_NAME(UTF8_STRING)' in v for v in properties.values()),'title types retained')
require('native-startup-diagnostic-04/error.txt' not in files,'candidate preparation succeeded')
require('sheet.xlsx' in files['native-startup-diagnostic-04/windows.txt'].decode(),'candidate recognized document')
good='native-node-relay-02'
for id in range(1,9):
    request=read(good+f'-evidence/request-{id}.json');row,payload=reply(good,id)
    require(request['id']==row['id']==id and row['tool']==request['tool'],'request identity')
    if payload.get('image_status')=='image':
        images=[c for c in row['result']['content'] if c['type']=='image']
        require(len(images)==1,'image in same response')
        image=base64.b64decode(images[0]['data'],validate=True)
        ref=payload['image_reference']
        require(hashlib.sha256(image).hexdigest()==ref['sha256'],'response image digest')
        require(image==files[good+'/run/'+ref['relative_path']],'response image equals retained capture')
_,refused=reply(good,2)
require(refused['outcome_summary']['target_refusal']['input_dispatched'] is False,'refusal before input')
_,finished=reply(good,7)
require(finished['receipt']['native_result']['evaluation']['actual']==[835,780],'reported saved values')
require(finished['outcome_summary']['evaluation_success'] is True,'evaluation success')
_,terminal=reply(good,8)
require(terminal['allocation']['status']=='terminal' and terminal['allocation']['returncode']==0,'owner terminal')
require(read(good+'-evidence/SUMMARY.json')['relay_exit_code']==0,'relay terminal')
with zipfile.ZipFile(io.BytesIO(files[good+'/run/sheet.xlsx'])) as workbook:
    sheet=ET.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
cells={c.attrib['r']:c.find('s:v',ns).text for c in sheet.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
require(cells.get('A1')=='835' and cells.get('A2')=='780','independent saved XML values')
print(f'PASS {len(files)} retained files; startup failure, title diagnosis and successful self-use reconcile')