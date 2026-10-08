import base64,hashlib,json,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
def require(ok,msg):
    if not ok:raise ValueError(msg)
p=Path(__file__).resolve().parent;m=json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as t:
    members=t.getmembers();require(all(x.isfile() for x in members),'regular members')
    require(len({x.name for x in members})==len(members),'unique names')
    data={x.name:t.extractfile(x).read() for x in members}
require(set(data)==set(m['files']),'exact files')
for n,b in data.items():require({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}==m['files'][n],n)
prefix='results-local/inkscape-numeric-primary-01/'
load=lambda n:json.loads(data[prefix+n])
req=[load(f'host/request-{i}.json') for i in range(1,7)]
require([x['tool'] for x in req]==['interface_observe']+['interface_dispatch']*4+['interface_close'],'six calls')
for i in range(1,7):
    reply=load(f'host/reply-{i}.json')['result'];require(reply['isError'] is False,'MCP error')
    if i<=5:
        pics=[x for x in reply['content'] if x['type']=='image'];require(len(pics)==1,'one image')
        review=load(f'host/review-{i}.json')
        require(review['reply_sha256']==hashlib.sha256(data[prefix+f'host/reply-{i}.json']).hexdigest(),'review reply')
        require(review['images']==[{'mime_type':'image/png','sha256':hashlib.sha256(base64.b64decode(pics[0]['data'],validate=True)).hexdigest()}],'review image')
    if i in (2,3,4,5):
        body=json.loads(next(x['text'] for x in reply['content'] if x['type']=='text'))
        result=body['receipt']['source']['raw_report']['result']
        require(result['status']=='completed' and result['recovery_required'] is False,'program completed')
        releases=result['execution']['releases'];require(bool(releases),'release present')
        require(all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases),'released')
require([x['arguments']['program']['program_id'] for x in req[1:5]]==['select-rectangle','select-x-value','set-x-80','save-svg'],'program order')
ops=req[3]['arguments']['program']['ops']
require([x['text'] for x in ops if x['op']=='text']==['80'],'numeric input')
rects=[x for x in ET.fromstring(data[prefix+'saved.svg']).iter() if x.tag.split('}')[-1]=='rect']
require(len(rects)==1,'single rectangle')
a=rects[0].attrib
for k,v in [('x',80),('y',50),('width',40),('height',30)]:require(abs(float(a[k])-v)<.1,k)
require('transform' not in a and a.get('fill')=='#ff0000','geometry and color')
require(load('evaluation.json')['success'] and load('host/exit.json')['code']==0,'oracle/relay')
timing=load('host-timing.json');require(timing['call_count']==6 and timing['timeline_status']=='complete','timeline')
for n,h in timing['input_sha256'].items():require(hashlib.sha256(data[prefix+'host/'+n]).hexdigest()==h,'timing identity')
print(f'PASS: {len(data)} pinned files; 6 calls, 4 input programs, 5 reviewed images; saved X80/Y50/40x30/red')
