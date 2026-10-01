from pathlib import Path
import hashlib,json,tarfile,tempfile,importlib.util
def require(ok,msg):
    if not ok:raise ValueError(msg)
root=Path(__file__).resolve().parent
with tarfile.open(root/'candidate.tar.gz') as t:
    members=t.getmembers();require(all(m.isfile() for m in members),'files only')
    require(len({m.name for m in members})==len(members),'unique paths')
    data={m.name:t.extractfile(m).read() for m in members}
manifest=json.loads(data['manifest.json'])
require(set(data)==set(manifest['files'])|{'manifest.json'},'exact members')
for n,h in manifest['files'].items():require(hashlib.sha256(data[n]).hexdigest()==h,n)
result=json.loads(data['result.json']);require(result==json.loads((root/'result.json').read_text()),'summary identity')
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'candidate.py';p.write_bytes(data['candidate/runtime/cli_v1/public_presentation.py'])
    spec=importlib.util.spec_from_file_location('archived_brief',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for row in result['rows']:
        parts=Path(row['source']).parts
        name='inputs/'+parts[1]+'/'+parts[-1]
        raw=data[name];require(hashlib.sha256(raw).hexdigest()==row['source_sha256'],'input identity')
        reply=json.loads(raw)
        view=json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text'))
        before=json.dumps(view,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        candidate=mod.brief_public_report(view)
        after=json.dumps(candidate,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        require(len(before)==row['full_bytes'] and len(after)==row['candidate_bytes'],'measured bytes')
        require(candidate['presentation']['returned']==row['returned'],'projection mode')
        require(json.dumps(view,sort_keys=True,separators=(',',':'),allow_nan=False).encode()==before,'input unchanged')
for name,total in result['totals'].items():
    rows=[r for r in result['rows'] if name in r['source']]
    require(sum(r['full_bytes'] for r in rows)==total['full_bytes'],'original total')
    require(sum(r['candidate_bytes'] for r in rows)==total['candidate_bytes'],'candidate total')
require('Ran 23 tests' in data['tests.log'].decode() and data['tests.log'].decode().rstrip().endswith('OK'),'focused tests')
print('PASS: seven retained replies; numeric +7 bytes, drag -104 bytes; adoption HOLD')
