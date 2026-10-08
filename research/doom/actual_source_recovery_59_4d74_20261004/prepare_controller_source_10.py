from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parent
repo=root.parent/'calc-construction-publication-4d74'
commit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=repo).decode().strip()
dest=root/'current-controller-source-10';dest.mkdir(exist_ok=False)
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'research/doom','research/live_control','research/real_apps_v1','research/observation_tiles','research/observation_gating'],cwd=repo).decode().splitlines()
assets=['research/doom/map01_cover_policy_schema_v6.json','research/doom/map01_motor_responder_v10.txt']
paths=[p for p in paths if (p.endswith('.py') and len(p.split('/'))==3) or p in assets]
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=repo,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
members={}
for p in paths:
    proc.stdin.write((commit+':'+p+'\n').encode());proc.stdin.flush()
    header=proc.stdout.readline().decode().split();data=proc.stdout.read(int(header[2]))
    assert proc.stdout.read(1)==b'\n'
    target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    members[p]={'sha256':hashlib.sha256(data).hexdigest(),'git_blob':header[0],'bytes':len(data)}
proc.stdin.close();assert proc.wait()==0
entry=(root/'portable_controller_entry_05.py').read_bytes()
old=b'526f6ef9f07953c053cc3eed136b1c1144e071dd35c0b9493b0c9820889ddefe'
assert old in entry
entry=entry.replace(old,members['research/doom/session_map01_v16.py']['sha256'].encode())
(root/'portable_controller_entry_06.py').write_bytes(entry)
driver=(root/'run_controller_relay_05.py').read_bytes().replace(b'current-controller-source-09',b'current-controller-source-10').replace(b'portable_controller_entry_05.py',b'portable_controller_entry_06.py').replace(b'run_controller_relay_05.py',b'run_controller_relay_06.py')
(root/'run_controller_relay_06.py').write_bytes(driver)
record={'status':'PREPARED_NOT_EXECUTED','source_commit':commit,'members':members,'entry_sha256':hashlib.sha256(entry).hexdigest(),'driver_sha256':hashlib.sha256(driver).hexdigest()}
(root/'CONTROLLER_SOURCE_10_PREPARATION.json').write_bytes(json.dumps(record,indent=2,sort_keys=True).encode())
config={'allocation_id':'59-4d74-source-refresh-lifecycle-construction01-20261004','max_seconds':120,'output_directory':'controller-recovery-01','host_workspace':'controller-recovery-01-host-empty','container_name':'ai59-4d74-recovery01','iterations':3,'seed':40121,'session_span':3,'model':'gpt-5.6-luna','effort':'low'}
(root/'controller_recovery_01.json').write_bytes(json.dumps(config,indent=2).encode())
print(json.dumps({'source_commit':commit,'members':len(members),'session_sha256':members['research/doom/session_map01_v16.py']['sha256'],'entry_sha256':record['entry_sha256'],'driver_sha256':record['driver_sha256']}))
