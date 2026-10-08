"""Independent readback of frozen A02 sources, receipts, and decision gates."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
run=p/'run-20261005T03'; manifest=json.loads((p/'source-manifest.json').read_text())
checks=[]
def check(name,ok): checks.append({'check':name,'ok':bool(ok)})
artifact_manifest=json.loads((p/'artifact-manifest.json').read_text())
check('SHA256SUMS agrees with artifact manifest', (p/'SHA256SUMS').read_text()==''.join(f"{v['sha256']}  {name}\n" for name,v in artifact_manifest['files'].items()))
check('all packaged artifacts match size and SHA-256 manifest', all((lambda b,r: len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'])((p/name).read_bytes(),record) for name,record in artifact_manifest['files'].items()))
check('all frozen source blobs match size and SHA-256', all((lambda b,r: len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'])((p/'source-snapshots'/(name+'.txt')).read_bytes(),record) for name,record in manifest['files'].items()))
rows=json.loads((run/'run-status.json').read_text())
check('three route probes exited zero', [x['route'] for x in rows]==['v12-perkey','v15-default','v15-perkey'] and all(x['exit_code']==0 for x in rows))
results={}
for route in ('v12-perkey','v15-default','v15-perkey'):
    result=json.loads((run/route/'result.json').read_text()); results[route]=result
    stdout=(run/(route+'.stdout.txt')).read_text().strip()
    check(route+' imported production paths are covered by frozen source manifest', set(result['actual_import_files'].values()).issubset(set(manifest['files'])))
    check(route+' stdout equals retained result', stdout==json.dumps(result,sort_keys=True))
    check(route+' stopped before construction with no forbidden calls',result['source_selection_finished'] and not result['session_started'] and not result['owner_instantiated'] and not result['forbidden_calls'])
expected='research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py'
a=results['v12-perkey']; b=results['v15-default']; c=results['v15-perkey']
check('V12 per-key selects archived A01 owner and matching recorded hash',a['owner_file']==expected and a['owner_sha256']==a['recorded_a01_owner_sha256']==a['expected_a01_owner_sha256'])
check('default V15 retains release-batch backend and V4 owner binding','doom_owner_thread_release_batch_backend_v1.Backend' in b['backend_mro'] and b['backend_owner_binding_file']=='research/live_control/input_transition_owner_v4.py')
check('V15 per-key fails owner identity despite archived A01 manifest hash',c['backend_owner_binding_file']=='research/live_control/input_owner_v12.py' and c['owner_sha256']!=c['recorded_a01_owner_sha256']==c['expected_a01_owner_sha256'])
status='FAIL_REPAIR_INEFFECTIVE_AT_4158d9b' if all(x['ok'] for x in checks) else 'INCONCLUSIVE_READBACK_FAILURE'
result={'schema':'v15_perkey_postrepair_a02_readback_v1','candidate_head':json.loads((p/'PLAN.json').read_text())['candidate_head'],'status':status,'checks':checks,'route_summary':{k:{'owner_file':v['owner_file'],'owner_sha256':v['owner_sha256'],'backend_owner_binding_file':v['backend_owner_binding_file'],'recorded_a01_owner_sha256':v['recorded_a01_owner_sha256'],'backend_mro':v['backend_mro']} for k,v in results.items()},'scope':'startup source-selection boundary only; no Session or owner instance, GUI, game, input, physical release, timing, task effect, or live threat exposure'}
(p/'audit-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':status,'checks':len(checks),'passed':sum(x['ok'] for x in checks)},sort_keys=True))
sys.exit(0 if all(x['ok'] for x in checks) else 1)
