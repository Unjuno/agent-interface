"""Check additive dependency reconstruction and retained audit parity; no execution."""
import hashlib,json,tarfile
from pathlib import Path

def require(value,message):
    if not value:raise ValueError(message)

def read_bundle(root):
    manifest=json.loads((root/'manifest.json').read_text());raw={}
    with tarfile.open(root/'raw.tar.gz') as archive:
        members=archive.getmembers()
        require(len(members)==len(manifest) and {m.name for m in members}==set(manifest),'members')
        for member in members:
            require(member.isfile(),'regular files')
            data=archive.extractfile(member).read();raw[member.name]=data
            require(len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256'],'bytes')
    return raw

root=Path(__file__).resolve().parent
current=read_bundle(root);prior=read_bundle(root.parent/'lifecycle-intake-01')
p='results-local/lifecycle-reference-reconstruction-01/'
q='results-local/lifecycle-intake-01/'
load=lambda name:json.loads(current[p+name])
source_manifest=json.loads(prior[q+'source-manifest.json'])
changes={row['path']:row for row in load('reconstruction.json')['changes']}
require(set(changes)=={'research/analysis/needle_role_skill_lifecycle_4916_v2/lifecycle.py','research/needle_role_skill_reload_3780_v1/loader.py'},'only two declared dependencies')
for path in source_manifest['files']:
    before=prior[q+'source/'+path];after=current[p+'source/'+path]
    if path in changes:
        row=changes[path]
        require(hashlib.sha256(before).hexdigest()==row['input_sha256'],'mapping input')
        require(hashlib.sha256(after).hexdigest()==row['output_sha256'],'mapping output')
        require(before.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')==after,'only line ending change')
    else:
        require(before==after,'all other source and evidence immutable')
suite='source/research/analysis/needle_role_skill_lifecycle_5133_v2/'
freeze=load(suite+'FREEZE.json')
for name,path in freeze['reference_sources'].items():
    require(hashlib.sha256(current[p+'source/'+path]).hexdigest()==freeze['reference_sources_sha256'][name],'exact frozen dependency')
checks=load('checks.json')
require(len(checks)==2 and all(c['returncode']==0 for c in checks),'tests and raw audit exit')
require(b'Ran 10 tests' in current[p+'check-1.stderr'] and b'\nOK\n' in current[p+'check-1.stderr'],'ten tests')
retained=load(suite+'results/audit-correction-04/correction.json');actual=load('correction.json')
require({k:v for k,v in retained.items() if k!='auditor_python'}=={k:v for k,v in actual.items() if k!='auditor_python'},'retained corrected audit parity')
require(actual['status']=='PASS_CORRECTED_RAW_REAUDIT_SCOPED' and actual['errors']==[],'scoped audit status')
require(actual['reconciled_predictions']==30000 and actual['mutation_controls_rejected']==7,'raw evidence coverage')
require(load('comparison.json')['identical_except_python_version'],'comparison')
print(f'PASS: {len(current)} files; exact dependency reconstruction, ten tests, corrected raw audit parity; not interface performance')
