import base64,hashlib,io,json,tarfile,zipfile
from pathlib import Path

def require(ok,message):
    if not ok:raise ValueError(message)
p=Path(__file__).resolve().parent;m=json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as t:
    members=[x for x in t.getmembers() if x.isfile()]
    require(len({x.name for x in members})==len(members),'duplicate member')
    data={x.name:t.extractfile(x).read() for x in members}
require(set(data)==set(m['files']),'members')
for name,raw in data.items():
    require({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}==m['files'][name],name)
b='results-local/inspection-error-flag-primary-01/'
load=lambda name:json.loads(data[b+name])
reply=lambda i:load(f'host/reply-{i}.json')
report=lambda i:json.loads(next(c['text'] for c in reply(i)['result']['content'] if c['type']=='text'))
require([load(f'host/request-{i}.json')['tool'] for i in (1,2,3)]==['interface_inspect_target','interface_review_target','interface_close'],'no input program')
require([reply(i)['result']['isError'] for i in (1,2,3)]==[False,True,False],'actual MCP flags')
for i in (1,2):
    body=report(i)
    require(body['status']=='needs_review' and body['input_dispatched'] is False and body['authority_granted'] is False,'pending review without input')
    require(body['session']['binding_revision']==1,'no selection revision')
require(report(1)['session']['targets']==report(2)['session']['targets'],'unchanged target')
require(report(1)['image_status']=='image' and report(1)['review_request']['tool']=='interface_review_target','successful inspection')
require('mismatched target review' in report(2)['error'] and 'review_request' not in report(2),'failed review')
receipt=load('host/review-1.json')
require(receipt['reply_sha256']==hashlib.sha256(data[b+'host/reply-1.json']).hexdigest(),'review identity')
pics=[c for c in reply(1)['result']['content'] if c['type']=='image'];require(len(pics)==1,'one image')
digest=hashlib.sha256(base64.b64decode(pics[0]['data'],validate=True)).hexdigest()
require(receipt['images']==[{'mime_type':'image/png','sha256':digest}],'reviewed image')
require(report(3)['status']=='closed' and report(3)['release_attempted'] is False and load('host/exit.json')['code']==0,'read-only close')
old=json.loads(data['results-local/reviewed-image-pair-01/B0-full/host/reply-4.json'])
body=json.loads(old['result']['content'][0]['text'])
require(old['result']['isError'] is True and body['status']=='needs_review' and 'review_request' in body and body['image_status']=='image','retained motivating response')
build='results-local/inspection-error-flag-build-01/'
manifest=json.loads(data[build+'manifest.json'])
require(manifest['source_revision']==m['source_commit'],'build source')
require(hashlib.sha256(data[build+'runtime.pyz']).hexdigest()==manifest['sha256'],'archive hash')
with zipfile.ZipFile(io.BytesIO(data[build+'runtime.pyz'])) as z:
    require(z.read('runtime/cli_v1/mcp_server.py')==data['runtime/cli_v1/mcp_server.py'],'built changed source')
checks=json.loads(data['results-local/inspection-error-flag-native-01/result.json'])
require(checks['status']=='PASS' and all(x['returncode']==0 for x in checks['suites']),'native checks')
before=data['results-local/inspection-error-flag-01/before.log'].decode()
after=data['results-local/inspection-error-flag-01/after.log'].decode()
require('FAILED (failures=2)' in before and 'ready_metadata' in before and 'ready_image' in before,'reproduced prior behavior')
require('Ran 22 tests' in after and after.rstrip().endswith('OK'),'focused checks')
timing=load('host-timing.json');require(timing['call_count']==3 and timing['timeline_status']=='complete','timeline')
for name,digest in timing['input_sha256'].items():
    require(hashlib.sha256(data[b+'host/'+name]).hexdigest()==digest,'timeline files')
print(f'PASS: {len(data)} files; original false-error reproduced, live flags false/true/false, no input or selection, exact portable source')
