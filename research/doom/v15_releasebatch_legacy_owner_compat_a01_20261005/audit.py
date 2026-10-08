"""Independent readback of frozen release-batch/owner protocol evidence."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent; checks=[]
def check(name,ok): checks.append({'check':name,'ok':bool(ok)})
artifact_manifest=json.loads((p/'artifact-manifest.json').read_text()); packaged_files=artifact_manifest['files']; manifest_file_ok=True
for rel,record in packaged_files.items():
 data=(p/rel).read_bytes()
 if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']: manifest_file_ok=False
check('all packaged artifacts match the frozen artifact manifest',manifest_file_ok)
check('SHA256SUMS agrees with the artifact manifest',''.join(f"{packaged_files[name]['sha256']}  {name}\n" for name in sorted(packaged_files))==(p/'SHA256SUMS').read_text())
manifest=json.loads((p/'source-manifest.json').read_text()); result=json.loads((p/'run-01/result.json').read_text()); plan=json.loads((p/'PLAN.json').read_text()); package_result=json.loads((p/'RESULT.json').read_text()); run=json.loads((p/'run-01/exit.json').read_text()); stdout=(p/'run-01/stdout.txt').read_text().strip(); output=json.loads(stdout)
verified=True
for rel,record in manifest['files'].items():
 data=(p/'source-snapshots'/(rel+'.txt')).read_bytes()
 if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']: verified=False
check('all frozen source snapshots match byte counts and SHA-256',verified)
files={rel:(p/'source-snapshots'/(rel+'.txt')).read_text() for rel in manifest['files']}
backend=files['research/doom/doom_owner_thread_release_batch_backend_v1.py']; archived=files['research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py']; current=files['research/live_control/input_owner_v12.py']
check('release-batch implementation requires up_batch', '"up_batch", self.lease, [item["key"] for item in pending]' in backend)
check('archived owner dispatch has no up_batch implementation', "op == 'up_batch'" not in archived and 'def release_keys_batch' not in archived)
check('current owner has the batch implementation', "op == 'up_batch'" in current and 'def release_keys_batch' in current)
check('run stdout equals retained result', output==result)
check('probe exit receipt is zero and output names the frozen archived owner', run['exit_code']==0 and result['archived_owner_file']=='research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py')
check('actual archived-owner call rejects up_batch as recorded', result['exception_type']=='ValueError' and result['exception_message']=='unknown input operation')
check('owner/display close and join completed with no XTest call', result['owner_closed'] and not result['owner_thread_alive'] and result['display_closed'] and result['forbidden_calls']==[])
check('decision gates match observed FAIL_COMPATIBILITY', plan['D'].startswith('FAIL_COMPATIBILITY') and result['status']=='FAIL_COMPATIBILITY')
check('run record pins executed probe', json.loads((p/'RUN.json').read_text())['probe_sha256']==hashlib.sha256((p/'probe_compat.py').read_bytes()).hexdigest())
status='PASS_COMPATIBILITY_FAILURE_REPRODUCED' if all(x['ok'] for x in checks) else 'FAIL_READBACK'
audit={'schema':'v15_releasebatch_legacy_owner_compat_a01_audit_v1','status':status,'checks':checks,'scope':package_result['scope']}
(p/'AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':status,'passed':sum(x['ok'] for x in checks),'checks':len(checks)},sort_keys=True));sys.exit(0 if all(x['ok'] for x in checks) else 1)
