import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def require(ok,message):
    if not ok:raise ValueError(message)
p=Path(__file__).resolve().parent;m=json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as t:
    data={x.name:t.extractfile(x).read() for x in t.getmembers() if x.isfile()}
require(set(data)==set(m['files']),'members')
for name,raw in data.items():
    require(len(raw)==m['files'][name]['bytes'] and hashlib.sha256(raw).hexdigest()==m['files'][name]['sha256'],name)
b='results-local/calc-review-request-primary-01/'
load=lambda name:json.loads(data[b+name])
report=lambda i:json.loads(next(c['text'] for c in load(f'host/reply-{i}.json')['result']['content'] if c['type']=='text'))
require(load('evaluation.json')=={'actual':[442,351],'expected':[442,351],'success':True},'evaluation')
with zipfile.ZipFile(io.BytesIO(data[b+'saved.xlsx'])) as z:
    root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
values={x.attrib['r']:x.find('s:v',ns).text for x in root.findall('.//s:c',ns) if x.find('s:v',ns) is not None}
require(values.get('A1')=='442' and values.get('A2')=='351','independent XML')
request=load('host/request-5.json');offered=report(4)['review_request']
require(request['tool']==offered['tool'] and request['arguments']==offered['arguments'],'exact offered request')
require(report(4)['binding_revision']==1 and report(5)['binding_revision']==2 and report(5)['capture_consistency']=='matched','selection')
for i in (2,3,6):
    s=report(i)['outcome_summary']
    require(s['execution_status']=='completed' and s['input_release_verified'] is True,'input completion')
for i in (1,2,3,4,5,7,8):
    reply=load(f'host/reply-{i}.json');review=load(f'host/review-{i}.json')
    require(review['source_sequence'] is None and review['schema']=='agent-interface/primary-review-receipt-v2-public-capture','public review')
    require(review['reply_sha256']==hashlib.sha256(data[b+f'host/reply-{i}.json']).hexdigest(),'reply hash')
    images=[c for c in reply['result']['content'] if c['type']=='image'];require(len(images)==1,'image count')
    digest=hashlib.sha256(base64.b64decode(images[0]['data'],validate=True)).hexdigest()
    require(digest==review['images'][0]['sha256']==review['capture']['artifact_sha256'],'image hash')
require(report(9)['status']=='closed' and report(9)['release']['verified'] is True,'closed')
require(load('host/exit.json')['code']==0,'relay exit')
summary=load('host-timing.json');require(summary['call_count']==9 and summary['timeline_status']=='complete','timeline')
for name,digest in summary['input_sha256'].items():
    require(hashlib.sha256(data[b+'host/'+name]).hexdigest()==digest,'timeline input')
cost=load('request-text-cost.json');added=0
for row in cost['rows']:
    value=report(row['attempt']);short={k:v for k,v in value.items() if k not in ('review_request','review_request_scope')}
    delta=len(json.dumps(value).encode())-len(json.dumps(short).encode())
    require(delta==row['added_bytes'],'response bytes');added+=delta
require(added==cost['added_bytes_total']==1335,'total cost')
checks=json.loads(data['results-local/target-review-request-native-01/result.json'])
require(checks['status']=='PASS' and all(x['returncode']==0 for x in checks['suites']),'native checks')
print(f'PASS: {len(data)} retained files; nine calls, seven reviews, exact selected request, XLSX 442/351; 1335 added text bytes')
