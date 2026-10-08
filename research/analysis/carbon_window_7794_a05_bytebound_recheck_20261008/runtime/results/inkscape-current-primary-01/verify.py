import base64,hashlib,json,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
def require(ok,msg):
    if not ok: raise ValueError(msg)
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as t:
    members=t.getmembers()
    require(all(x.isfile() for x in members),'regular files only')
    require(len({x.name for x in members})==len(members),'unique names')
    data={x.name:t.extractfile(x).read() for x in members}
require(set(data)==set(m['files']),'exact member set')
for n,b in data.items():
    require({'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}==m['files'][n],n)
prefix='results-local/inkscape-current-primary-01/'
load=lambda n:json.loads(data[prefix+n])
requests=[load(f'host/request-{i}.json') for i in range(1,6)]
require([x['tool'] for x in requests]==['interface_observe','interface_dispatch','interface_dispatch','interface_dispatch','interface_close'],'call sequence')
for i in range(1,6):
    r=load(f'host/reply-{i}.json')['result']
    require(not r.get('isError',False),'MCP error')
    if i<=4:
        pics=[c for c in r['content'] if c['type']=='image']
        require(len(pics)==1,'one image')
        review=load(f'host/review-{i}.json')
        require(review['reply_sha256']==hashlib.sha256(data[prefix+f'host/reply-{i}.json']).hexdigest(),'review reply identity')
        require(review['images']==[{'mime_type':'image/png','sha256':hashlib.sha256(base64.b64decode(pics[0]['data'],validate=True)).hexdigest()}],'review image identity')
    if i in (2,3,4):
        body=json.loads(next(c['text'] for c in r['content'] if c['type']=='text'))
        result=body['receipt']['source']['raw_report']['result']
        require(result['status']=='completed' and not result['recovery_required'],'completed dispatch')
        require(all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in result['execution']['releases']),'released inputs')
ops=requests[2]['arguments']['program']['ops']
moves=[x for x in ops if x['op']=='pointer_move']
require([x['x'] for x in moves]==[620,632,644,656] and all(x['y']==391 for x in moves),'actual commanded path')
rects=[x for x in ET.fromstring(data[prefix+'saved.svg']).iter() if x.tag.split('}')[-1]=='rect']
require(len(rects)==1,'single rectangle')
r=rects[0]
require(float(r.attrib['x'])>50.5 and 'transform' not in r.attrib,'rightward translation')
for n,v in [('y',50),('width',40),('height',30)]:
    require(abs(float(r.attrib[n])-v)<=.1,n)
require(r.attrib.get('fill') in ('red','#ff0000'),'fill')
require(load('evaluation.json')['success'] is True,'recorded oracle')
require(load('host/exit.json')['code']==0,'relay exit')
timing=load('host-timing.json')
require(timing['timeline_status']=='complete' and timing['call_count']==5,'timeline')
for n,h in timing['input_sha256'].items():
    require(hashlib.sha256(data[prefix+'host/'+n]).hexdigest()==h,'timing input identity')
require(all(c['presentations'][0]['image_delivery']['mode']=='full' for c in timing['calls']),'no reuse references')
print(f'PASS: {len(data)} pinned files; 5 calls, 3 completed programs, 4 reviewed images; saved SVG task oracle')
