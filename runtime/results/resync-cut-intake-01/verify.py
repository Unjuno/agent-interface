import hashlib,json,tarfile
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
    require({'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}==m['files'][name],name)
load=lambda n:json.loads(data[n])
r=load('result.json');require((p/'result.json').read_bytes()==data['result.json'],'published result')
for path,digest in r['source_pins'].items():
    require(hashlib.sha256(data['current-source/'+path]).hexdigest()==digest,'current source pin')
intake=load('intake.json')
for path,digest in intake['files'].items():
    require(hashlib.sha256(data['package/'+Path(path).name]).hexdigest()==digest,'package source pin')
runs=load('container.stdout.json')['runs']
require(all(row['returncode']==0 for row in runs.values()),'run exits')
require(runs['audit']['stdout'].encode()==data['evidence/AUDIT.json'],'audit exact match')
require(runs['controls']['stdout'].encode()==data['evidence/CONTROLS.json'],'controls exact match')
audit=json.loads(runs['audit']['stdout']);controls=json.loads(runs['controls']['stdout'])
require(audit['decision']=='PASS_X11_RESYNC_CUT_SCOPED' and audit['checks']==2478 and audit['errors']==[],'raw audit')
require(controls['pass'] is True and controls['count']==12 and all(x['changed'] and x['pass'] for x in controls['results']),'effective controls')
require('Ran 7 tests' in runs['policy_tests']['stderr'] and runs['policy_tests']['stderr'].rstrip().endswith('OK'),'policy tests')
container=load('container-inspect.json')[0];host=container['HostConfig'];state=container['State']
require(state['Status']=='exited' and state['ExitCode']==0 and not state['OOMKilled'],'container terminal')
require(container['Image']==r['docker_image'],'pinned image')
require(host['NetworkMode']=='none' and host['ReadonlyRootfs'] is True and host['Memory']==268435456 and host['PidsLimit']==64,'container isolation')
require(all(not mount['RW'] for mount in container['Mounts'] if mount['Type']=='bind'),'read-only inputs')
require(load('exit.json')=={'docker_start_exit':0,'container_exit':0},'outer exit')
require(r['status']=='RETAINED_EVIDENCE_PASS_SHARED_RUNTIME_ADOPTION_HOLD' and r['new_x11_sessions']==0,'scope')
print(f'PASS: {len(data)} files; Docker raw-only audit 2478 checks, 12 effective controls, 7 policy tests; runtime adoption HOLD')
