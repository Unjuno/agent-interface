"""Verify the retained source-provenance integration evidence without extraction."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).parent
def require(ok,why):
    if not ok:raise ValueError(why)
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers()
    require(all(m.isfile() for m in members),'regular files')
    require(len(members)==len({m.name for m in members}),'unique names')
    files={m.name:archive.extractfile(m).read() for m in members}
manifest=json.loads((root/'manifest.json').read_text())
require(set(files)==set(manifest),'inventory')
for name,digest in manifest.items():require(hashlib.sha256(files[name]).hexdigest()==digest,name)
report=json.loads(files['guarded-source-provenance-01/REPORT.json'])
require(report['writer_count']==len(report['writers'])==32,'writers')
for name,digest in report['source_hashes'].items():
    require(hashlib.sha256(files['candidate/research/live_control/'+name]).hexdigest()==digest,name)
for name,digest in report['example_after'].items():
    source=('candidate/'+name[6:] if name.startswith('../../') else 'candidate/research/live_control/'+name)
    require(hashlib.sha256(files[source]).hexdigest()==digest,'example source '+name)
require(len(report['example_after'])-len(report['example_before'])==8,'moved source additions')
check=json.loads(files['guarded-source-provenance-check-01/result.json'])
require(check['status']=='PASS' and all(r['returncode']==0 for r in check['suites']),'integration checks')
for suite in check['suites']:
    for log in suite['logs'].values():
        require(hashlib.sha256(files['guarded-source-provenance-check-01/'+log['file']]).hexdigest()==log['sha256'],'log identity')
print(f'PASS {len(files)} files; 32 producer updates, shared implementation hashes, retained checks')
