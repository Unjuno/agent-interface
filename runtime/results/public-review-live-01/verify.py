import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def require(ok, message):
    if not ok: raise ValueError(message)
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as t:
    data={x.name:t.extractfile(x).read() for x in t.getmembers() if x.isfile()}
require(set(data)==set(m['files']), 'member set')
for name, raw in data.items():
    require(len(raw)==m['files'][name]['bytes'] and hashlib.sha256(raw).hexdigest()==m['files'][name]['sha256'], name)
prefix='results-local/calc-review-live-02/'
load=lambda n:json.loads(data[prefix+n])
require(load('evaluation.json')=={'actual':[804,592],'expected':[804,592],'success':True},'oracle')
with zipfile.ZipFile(io.BytesIO(data[prefix+'saved.xlsx'])) as z:
    root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
values={c.attrib['r']:c.find('s:v',ns).text for c in root.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
require(values.get('A1')=='804' and values.get('A2')=='592','saved XML')
require(load('timing-before.json')['exit_code']!=0 and 'review receipt identity' in load('timing-before.json')['stderr'],'original failure')
summary=load('host-timing-after.json')
require(summary['call_count']==14 and summary['timeline_status']=='complete','timeline')
require(sum(len(c['reviews']) for c in summary['calls'])==9,'review count')
for name,digest in summary['input_sha256'].items():
    require(hashlib.sha256(data[prefix+'host/'+name]).hexdigest()==digest,'timeline input')
reviewed=[1,2,3,5,6,9,10,12,13]
for i in reviewed:
    reply=load(f'host/reply-{i}.json');review=load(f'host/review-{i}.json')
    require(review['schema']=='agent-interface/primary-review-receipt-v2-public-capture' and review['source_sequence'] is None,'review schema')
    require(review['reply_sha256']==hashlib.sha256(data[prefix+f'host/reply-{i}.json']).hexdigest(),'reply hash')
    images=[c for c in reply['result']['content'] if c['type']=='image']
    require(len(images)==1,'image count')
    digest=hashlib.sha256(base64.b64decode(images[0]['data'],validate=True)).hexdigest()
    require(digest==review['capture']['artifact_sha256']==review['images'][0]['sha256'],'image identity')
for i in [2,5,11]:
    reply=load(f'host/reply-{i}.json')
    report=json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'))
    require(report['outcome_summary']['execution_status']=='completed' and report['outcome_summary']['input_release_verified'] is True,'input completion')
require(load('host/exit.json')['code']==0,'relay exit')
require(json.loads(data['results-local/calc-review-live-01/failure.json'])['input_sent'] is False,'setup failure')
print(f'PASS: {len(data)} files; 14 replies, nine live public reviews, saved XML 804/592; no semantic timing claim')
