"""Read-only archive verification; never launches archived drivers or apps."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz') as archive:
    members=[m for m in archive if m.isfile()]
    if len({m.name for m in members})!=len(members):raise ValueError('duplicate members')
    files={m.name:archive.extractfile(m).read() for m in members}
def require(condition,message):
    if not condition:raise ValueError(message)
require(set(files)==set(manifest),'manifest coverage')
for name,digest in manifest.items():
    require(hashlib.sha256(files[name]).hexdigest()==digest,name)
def read(folder,path):return json.loads(files[folder+'/'+path].decode('utf-8-sig'))
b='native-owner-lifetime-construction-01';c='native-owner-lifetime-candidate-01';g='native-owner-lifetime-calc-01'
old=read(b,'observation.json')
require(old['server_after'] is None and old['survived_server_exit'] is True,'baseline survival')
new=read(c,'observation.json')
require(new['server_after'] is None and not new['survived_server_exit'],'candidate stopped')
require(read(c,'allocation/run/fixture-exit.json')['owner_ended'] is True,'EOF cause')
for folder in (b,c):
    cleanup=read(folder,'cleanup.json')
    require(cleanup['reaped_exit']==0 and cleanup['process_after'] is None and not cleanup['rescue_used'],'fixture cleanup')
result=read(g,'RESULT.json')
require(result['server_after'] is None and result['owner_after'] is None and result['owner_exit']==1,'GUI owner termination')
require('owning server ended' in result['error'],'GUI EOF cause')
require(result['requests']==[] and not result['external_rescue'],'no input/rescue')
require(result['cleanup']['tracked_processes_terminal'] is True,'tracked termination')
require(all(v is None for v in result['tracked_process_after'].values()),'tracked process absence')
require(read(g,'allocation/run/cleanup-report.json')==result['cleanup'],'cleanup consistency')
require(not any(n.startswith(g+'/allocation/run/request-') for n in files),'request inventory')
print(f'PASS {len(files)} files; baseline survival, candidate EOF and scoped Calc cleanup')
