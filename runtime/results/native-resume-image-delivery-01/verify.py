"""Verify retained paired retrieval without extraction or execution."""
import base64,hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).parent
def require(ok,why):
    if not ok:raise ValueError(why)
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members),'regular files only')
    require(len(members)==len({m.name for m in members}),'unique names')
    files={m.name:archive.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(files)==set(manifest),'inventory')
for name,digest in manifest.items():require(hashlib.sha256(files[name]).hexdigest()==digest,name)
def read(name):return json.loads(files[name])
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False)
a,b=[read(f'request-{i}.json') for i in (1,2)]
require(a['tool']==b['tool']=='native_resume','read-only calls')
require(a['arguments']=={k:v for k,v in b['arguments'].items() if k!='include_image'},'same request selection')
require(b['arguments']['include_image'] is False,'explicit omission')
require(a['arguments']['decision_sha256']==hashlib.sha256(files['original-request.json']).hexdigest(),'request digest')
responses=[read(f'reply-{i}.json') for i in (1,2)]
for i,row in enumerate(responses,1):
    require(row['status']=='returned' and row['id']==i and not row['result']['isError'],'returned identity')
full,omitted=[r['result']['content'] for r in responses]
require([c['type'] for c in full]==['text','image'] and [c['type'] for c in omitted]==['text'],'block counts')
x,y=json.loads(full[0]['text']),json.loads(omitted[0]['text'])
require(y['image_delivery']=='omitted_by_request','omission explicit')
for key in ('receipt','outcome_summary','image_status','image_reference','continuation','window_inventory'):
    require(canonical(x.get(key))==canonical(y.get(key)),key)
require(hashlib.sha256(base64.b64decode(full[1]['data'],validate=True)).hexdigest()==x['image_reference']['sha256'],'image digest')
require(x['exchange']['resumed_read_only'] is True and y['exchange']['resumed_read_only'] is True,'no new submission')
require(read('exit.json')['code']==0,'relay exit')
check=read('CHECK.json')
require(check['requestBytesUnchanged'] is True and check['requestMtimeUnchanged'] is True,'recorded unchanged source')
print(f'PASS {len(files)} files; exact-request outcomes match with image delivery 1 -> 0')