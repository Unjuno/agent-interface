"""Verify retained bytes and records only; never rerun archived code."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).parent
manifest=json.loads((root/'manifest.json').read_text())
def require(ok,why):
    if not ok:raise ValueError(why)
with tarfile.open(root/'raw.tar.gz') as archive:
    members=[m for m in archive if m.isfile()]
    require(len(members)==len({m.name for m in members}),'duplicate paths')
    files={m.name:archive.extractfile(m).read() for m in members}
require(set(files)==set(manifest),'manifest coverage')
for name,digest in manifest.items():require(hashlib.sha256(files[name]).hexdigest()==digest,name)
def read(folder,name):return json.loads(files[folder+'/'+name].decode('utf-8-sig'))
def reply(folder,name):return json.loads(read(folder,name+'.json')['content'][0]['text'])
k='native-owner-lifetime-calc-kill-01';s='native-explicit-stop-calc-01'
for folder in (k,s):
    retained=read(folder,'MANIFEST.json')
    require(set(retained)=={n[len(folder)+1:] for n in files if n.startswith(folder+'/') and n!=folder+'/MANIFEST.json'},'inner coverage')
    for name,digest in retained.items():require(hashlib.sha256(files[folder+'/'+name]).hexdigest()==digest,'inner digest')
    r=read(folder,'RESULT.json')
    require(r['requests']==[],'no input requests')
    require(not any(n.startswith(folder+'/allocation/run/request-') for n in files),'request inventory')
    require(folder+'/allocation/run/evaluation.json' not in files,'no success evaluation')
    require(r['cleanup']==read(folder,'allocation/run/cleanup-report.json'),'cleanup consistency')
    require(r['cleanup']['tracked_processes_terminal'] is True,'tracked terminal')
r=read(k,'RESULT.json');before=read(k,'before.json');kill=read(k,'server-kill.json')
require(kill['target']['pid']==before['ppid'] and kill['mechanism']=='pidfd_send_signal','kill target')
require(r['server_after'] is None and r['owner_after'] is None and r['owner_exit']==1,'kill termination')
require(all(v is None for v in r['tracked_process_after'].values()) and not r['external_rescue'],'kill cleanup')
start=reply(s,'start')['allocation'];stop=reply(s,'stop')['allocation'];end=reply(s,'stop-again')['allocation'];again=reply(s,'start-again')['allocation']
require(len({a['pid'] for a in (start,stop,end,again)})==1,'same owner')
require(stop['stop_requested'] is True and stop['status'] in ('stopping','terminal'),'stop requested')
require(end['status']==again['status']=='terminal' and end['returncode']==again['returncode']==1,'no relaunch')
r=read(s,'RESULT.json')
require(r['owner_absent'] and all(r['tracked_absent'].values()) and not r['evaluation_present'],'explicit stop cleanup')
require('native_stop' in {t['name'] for t in read(s,'tools-after.json')['tools']},'connection remained callable')
print(f'PASS {len(files)} files; idle server kill and explicit stop receipts reconcile')
