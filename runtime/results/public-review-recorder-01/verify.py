import base64,hashlib,json,tarfile
from pathlib import Path
def require(value,message):
    if not value:raise ValueError(message)
root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_text())['files'];raw={}
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers();require(len(members)==len(manifest) and {m.name for m in members}==set(manifest),'members')
    for member in members:
        require(member.isfile(),'regular file');data=archive.extractfile(member).read();raw[member.name]=data
        require(len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256'],'bytes')
with tarfile.open(root.parent/'calc-compact-primary-01/raw.tar.gz') as archive:
    prior={m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
p='results-local/public-review-retained-01/'
rows=json.loads(raw[p+'result.json'])['rows'];require(len(rows)==8,'eight replies')
require(sum(r['accepted'] for r in rows)==5,'five accepted')
for row in rows:
    data=prior[f"results-local/calc-compact-primary-01/host/reply-{row['attempt']}.json"]
    digest=hashlib.sha256(data).hexdigest();require(digest==row['reply_sha256'],'original reply')
    reply=json.loads(data);images=[c for c in reply['result']['content'] if c['type']=='image']
    require(bool(images)==row['accepted']==row['hasImage'],'image acceptance')
    if not row['accepted']:
        require(p+f"review-{row['attempt']}.json" not in raw,'no refused receipt');continue
    receipt=json.loads(raw[p+f"review-{row['attempt']}.json"])
    require(receipt['reply_sha256']==digest and receipt['source_sequence'] is None,'attribution without sequence')
    require(receipt['schema']=='agent-interface/primary-review-receipt-v2-public-capture','public schema')
    require(receipt['phase']=='retrospective-recorder-check','not new live review')
    image_hash=hashlib.sha256(base64.b64decode(images[0]['data'])).hexdigest()
    require(receipt['capture']['artifact_sha256']==image_hash==receipt['images'][0]['sha256'],'exact delivered image')
log=raw['results-local/public-review-tests-01/node-final.log'].decode()
require('tests 15' in log and 'pass 15' in log and 'fail 0' in log,'node checks')
print(f'PASS: {len(raw)} files; five exact public image attributions, three no-image refusals; no live timing claim')
