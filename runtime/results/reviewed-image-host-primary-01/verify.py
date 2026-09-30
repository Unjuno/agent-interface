import base64, hashlib, io, json, tarfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def require(ok, message):
    if not ok: raise ValueError(message)

p = Path(__file__).resolve().parent
manifest = json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as archive:
    members = [x for x in archive.getmembers() if x.isfile()]
    require(len({x.name for x in members}) == len(members), 'duplicate member')
    data = {x.name: archive.extractfile(x).read() for x in members}
require(set(data) == set(manifest['files']), 'members')
for name, raw in data.items():
    require({'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)} == manifest['files'][name], name)
b = 'results-local/calc-image-reuse-primary-01/'
load = lambda name: json.loads(data[b+name])
reply = lambda i: load(f'host/reply-{i}.json')
report = lambda i: json.loads(next(c['text'] for c in reply(i)['result']['content'] if c['type']=='text'))
require(load('evaluation.json') == {'actual':[346,291], 'expected':[346,291], 'success':True}, 'evaluation')
with zipfile.ZipFile(io.BytesIO(data[b+'saved.xlsx'])) as archive:
    xml = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
values = {c.attrib['r']:c.find('s:v',ns).text for c in xml.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
require(values.get('A1')=='346' and values.get('A2')=='291', 'independent saved XML')
require(reply(1)['result'].get('isError') is True, 'initial argument failure retained')
require('frame' in reply(1)['result']['content'][0]['text'] and 'region' in reply(1)['result']['content'][0]['text'], 'missing required arguments')
for i in (3,4,7):
    summary = report(i)['outcome_summary']
    require(summary['execution_status']=='completed' and summary['input_release_verified'] is True, 'input completion')
offered = report(5)['review_request']; submitted = load('host/request-6.json')
require(submitted['tool']==offered['tool'] and submitted['arguments']==offered['arguments'], 'exact offered target request')
require(report(6)['binding_revision']==2 and report(6)['capture_consistency']=='matched', 'target binding')
events = [json.loads(line) for line in data[b+'host/host-events.jsonl'].splitlines()]
base = None; active = None; last = None; images = []
for index, event in enumerate(events, 1):
    require(event['sequence']==index, 'event order')
    kind = event['kind']; i = event.get('attempt')
    if kind == 'presentation_started':
        require(active is None, 'presentation overlap')
        raw = data[b+f'host/reply-{i}.json']
        require(hashlib.sha256(raw).hexdigest()==event['reply_sha256'], 'presentation reply')
        picture = [c for c in reply(i)['result']['content'] if c['type']=='image']
        delivery = event['image_delivery']
        if delivery['mode'] == 'reviewed-image-reference':
            require(base is not None and delivery==base[0], 'reviewed base identity')
            require(len(picture)==1 and picture[0]['data']==base[1], 'exact image equality')
        else:
            require(delivery=={'mode':'full'}, 'full shape')
        active = (i, delivery, picture)
    elif kind == 'presentation_callbacks_completed':
        require(active is not None and active[:2]==(i,event['image_delivery']), 'completed identity')
        last = active; active = None
        if last[1]['mode']=='full': base = None
        for picture in last[2]:
            images.append({'attempt':i,'png_bytes':len(base64.b64decode(picture['data'],validate=True)),'mode':last[1]['mode']})
    elif kind == 'review_recorded':
        require(last is not None and last[:2]==(i,event['image_delivery']), 'reviewed presentation')
        receipt = load(f'host/review-{i}.json')
        require(receipt['source_sequence'] is None, 'no invented source sequence')
        require(receipt['reply_sha256']==hashlib.sha256(data[b+f'host/reply-{i}.json']).hexdigest(), 'review reply')
        require(len(last[2])==1, 'review image count')
        picture=last[2][0]; digest=hashlib.sha256(base64.b64decode(picture['data'],validate=True)).hexdigest()
        require(receipt['images']==[{'mime_type':'image/png','sha256':digest}], 'review image')
        if last[1]['mode']=='full':
            base=({'mode':'reviewed-image-reference','base_attempt':i,
                   'base_reply_sha256':receipt['reply_sha256'],
                   'base_review_sha256':hashlib.sha256(data[b+f'host/review-{i}.json']).hexdigest(),
                   'image_sha256':digest,'mime_type':'image/png'},picture['data'])
require(active is None, 'incomplete presentation')
cost=load('presentation-cost.json')
require(cost['images']==images and len(images)==7, 'image accounting')
require([x['attempt'] for x in images if x['mode']=='reviewed-image-reference']==[6], 'reference count')
require(cost['omitted_png_bytes']==77064 and cost['full_image_presentations']==6, 'presentation counts')
require(report(10)['status']=='closed' and report(10)['release']['verified'] is True and load('host/exit.json')['code']==0, 'relay cleanup')
timing=load('host-timing.json')
require(timing['call_count']==10 and timing['timeline_status']=='complete', 'timing')
for name,digest in timing['input_sha256'].items():
    require(hashlib.sha256(data[b+'host/'+name]).hexdigest()==digest, 'timing inputs')
checks=json.loads(data['results-local/reviewed-image-host-native-01/result.json'])
require(checks['status']=='PASS' and all(s['returncode']==0 for s in checks['suites']), 'native checks')
print(f'PASS: {len(data)} files; 10 calls, 7 images, 1 reviewed reference; saved XLSX 346/291')
