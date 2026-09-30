import hashlib,json,tarfile
from pathlib import Path
def require(ok, message):
    if not ok: raise ValueError(message)
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text())
with tarfile.open(p/'raw.tar.gz') as t:
    data={x.name:t.extractfile(x).read() for x in t.getmembers() if x.isfile()}
require(set(data)==set(m['files']), 'member set')
for name,raw in data.items():
    require(len(raw)==m['files'][name]['bytes'] and hashlib.sha256(raw).hexdigest()==m['files'][name]['sha256'],name)
base='results-local/refusal-scope-01/'
result=json.loads(data[base+'native/result.json'])
require(result['status']=='PASS' and all(x['returncode']==0 for x in result['suites']), 'native suites')
require(b'Ran 274 tests' in data[base+'native/protocol.stderr.log'], 'protocol count')
require(b'Ran 126 tests' in data[base+'native/harness.stderr.log'], 'harness count')
audit=json.loads(data[base+'interop-audit.json'])
require(audit['status']=='PASS_EXPECTED_COMPATIBILITY_FAILURES_REPRODUCED' and len(audit['observed_mismatches'])==6, 'interop failure gate')
for name in ['runtime/backends/x11_v1/session.py','runtime/cli_v1/review.py']:
    require((p.parents[2]/name).read_bytes()==data[name], 'current implementation identity')
print(f'PASS: {len(data)} retained files; 400 native checks and scoped interop HOLD')
