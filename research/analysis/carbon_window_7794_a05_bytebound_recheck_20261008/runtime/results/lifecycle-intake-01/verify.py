"""Verify retained integration STOP without executing source or rerunning science."""
import hashlib,json,tarfile
from pathlib import Path

def require(value,message):
    if not value:raise ValueError(message)

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(len(members)==len(manifest) and {m.name for m in members}==set(manifest),'members')
    for member in members:
        require(member.isfile(),'regular file')
        data=archive.extractfile(member).read();raw[member.name]=data
        require(len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256'],'bytes')
prefix='results-local/lifecycle-intake-01/'
load=lambda name:json.loads(raw[prefix+name])
checks=load('checks.json')
require(len(checks)==1 and checks[0]['returncode']==1,'test STOP and no audit')
require(b'Ran 10 tests' in raw[prefix+'check-1.stderr'] and b'FAILED (failures=1)' in raw[prefix+'check-1.stderr'],'test summary')
source=load('source-manifest.json')
for path,record in source['files'].items():
    data=raw[prefix+'source/'+path]
    require(hashlib.sha256(data).hexdigest()==record['sha256'],'snapshot source')
freeze=load('source/research/analysis/needle_role_skill_lifecycle_5133_v2/FREEZE.json')
for name,digest in freeze['sources'].items():
    require(hashlib.sha256(raw[prefix+'source/research/analysis/needle_role_skill_lifecycle_5133_v2/'+name]).hexdigest()==digest,'candidate source matches')
diagnostic=load('reference-diagnostic.json')
require(len(diagnostic)==2,'two references')
for row in diagnostic:
    data=raw[prefix+'source/'+row['path']]
    require(hashlib.sha256(data).hexdigest()==row['current']==row['base'],'reference bytes')
    require(row['current']!=row['expected'],'preserved mismatch')
    require(hashlib.sha256(data.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()==row['expected']==row['lf_to_crlf'],'representation mapping')
print(f'PASS retained HOLD verification: {len(raw)} files; candidate hashes match, two reference mismatches preserved')
