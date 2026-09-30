"""Verify the retained primary Calc task without executing the GUI or archived code."""
import hashlib,io,json,tarfile,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def require(value,message):
    if not value:raise ValueError(message)
root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(len(members)==len(manifest) and {m.name for m in members}==set(manifest),'member identities')
    for member in members:
        require(member.isfile(),'regular file')
        data=archive.extractfile(member).read();raw[member.name]=data
        require(len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256'],'bytes')
p='results-local/calc-compact-primary-01/'
load=lambda name:json.loads(raw[p+name])
reports=[];tools=[];images=0
for n in range(1,9):
    request=load(f'host/request-{n}.json');reply=load(f'host/reply-{n}.json')
    require(request['id']==reply['id']==n and request['tool']==reply['tool'],'identity')
    tools.append(request['tool']);shown=json.loads(reply['result']['content'][0]['text'])
    reports.append(shown.get('receipt',{}).get('source',{}).get('raw_report',shown))
    images+=sum(c['type']=='image' for c in reply['result']['content'])
    if request['tool'] in ('interface_observe','interface_dispatch'):
        require(request['arguments']['compact'] and request['arguments']['report_refs'],'explicit projection')
        require(shown['receipt']['schema']=='agent-interface/receipt-view-v3-report-ref','v3 returned')
    if n<8:
        require(load(f'primary-review-{n}.json')['reply_sha256']==hashlib.sha256(raw[p+f'host/reply-{n}.json']).hexdigest(),'review binding')
require(tools==['interface_observe','interface_dispatch','interface_dispatch','interface_inspect_target','interface_review_target','interface_dispatch','interface_inspect_target','interface_close'],'call order')
require(images==5,'five image deliveries')
require(len({x['session']['session_id'] for x in reports})==1,'owned connection')
for n in (1,2,5):
    result=reports[n]['result'];require(result['status']=='completed','input completed')
    release=result['execution']['releases'][-1]
    require(release['verified'] and release['keys_down']==[] and release['buttons_down']==[],'input released')
require(reports[4]['status']=='target_reviewed' and reports[4]['binding_revision']==2,'modal review')
require(reports[6]['evidence']['window_id']==reports[0]['session']['targets']['app'],'focused main returned')
require(reports[7]['status']=='closed' and reports[7]['release']['verified'],'close')
with zipfile.ZipFile(io.BytesIO(raw[p+'saved.xlsx'])) as book:
    sheet=ET.fromstring(book.read('xl/worksheets/sheet1.xml'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
values={c.attrib['r']:c.find('s:v',ns).text for c in sheet.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
require([values['A1'],values['A2']]==['336','439'],'independent XLSX values')
require(load('evaluation.json')['success'],'fixture evaluation')
require(load('host/exit.json')['code']==0,'normal relay exit')
require(all(x['returncode'] is not None for x in load('cleanup.json')),'owned processes reaped')
require(hashlib.sha256(raw['results-local/recovery-capture-build-01/runtime.pyz']).hexdigest()=='7962f327fad5d9ca63273c059e23c98186cdc7713766431f6d0418e97c987591','runtime archive')
print(f'PASS: {len(raw)} files; eight calls, five images, saved Calc 336/439; no speed or token claim')
