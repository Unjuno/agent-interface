"""Read-only portable MCP argument-refusal audit; no GUI success claim."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_text());raw={}
def check(ok,message):
 if not ok:raise SystemExit(message)
with tarfile.open(root/'raw.tar.gz') as archive:
 for m in archive.getmembers():
  check(m.isfile() and m.name in manifest and m.name not in raw,'unexpected member')
  data=archive.extractfile(m).read();expected=manifest[m.name]
  check(len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],'hash mismatch')
  raw[m.name]=data
check(set(raw)==set(manifest),'missing member')
def read(name):return json.loads(raw['results-local/'+name])
p='guarded-unknown-arguments-01/'
request=read(p+'transport/request-1.json');reply=read(p+'transport/reply-1.json')
check(request['arguments']['pointer'] is False and reply['result']['isError'] is True,'request and refusal')
row=json.loads(reply['result']['content'][0]['text'])
check(row['status']=='invalid_request' and row['unknown_arguments']==['pointer'] and row['operation_invoked'] is False and row['input_dispatched'] is False,'no input')
close=json.loads(read(p+'transport/reply-2.json')['result']['content'][0]['text'])
check(close['status']=='closed' and close['release_attempted'] is False and close['connection_close_attempted'] is False and close['session']['observation_sequence'] is None,'owner never initialized')
check(read(p+'transport/exit.json')['code']==0,'transport terminal')
check(read('guarded-brief-check-02/result.json')['status']=='PASS','local suites')
for name,count in [('protocol',247),('harness',106)]:
 log=raw[f'results-local/guarded-brief-check-02/{name}.stderr.log'].decode()
 check(f'Ran {count} tests' in log and log.rstrip().endswith('OK'),'suite counts')
build=read('guarded-brief-build-02/manifest.json')
check(build['source_revision']=='e609b197157f06e5cc6b4dd80049d88f842ebd6f','source')
check(hashlib.sha256(raw['results-local/guarded-brief-build-02/runtime.pyz']).hexdigest()==build['sha256'],'archive identity')
print(f'PASS: {len(raw)} files, portable MCP refusal before owner initialization, transport exit 0, 247+106 contract tests.')