from pathlib import Path
import json
root=Path('research/integration/live_xres_bystander_reuse_20261022_r01/raw/r01')
conditions=json.loads((root/'CONDITIONS.json').read_text(encoding='utf-8'))
result=json.loads((root/'result.json').read_text(encoding='utf-8'))
checks={
 'frozen_main_recorded':conditions['source_revision']=='cbd163342c2e8157a64d59f3f0a6c1e479c98bb4',
 'resource_base_reused_naturally':result.get('resource_base_reused') is True and result['owner']['resource_base']==result['bystander']['resource_base'],
 'distinct_process_identities':result['owner']['pid']!=result['bystander']['pid'] and result['supervisor']['pid'] not in (result['owner']['pid'],result['bystander']['pid']),
 'key_down_before_retirement':result.get('key_down_before_retirement') is True,
 'key_down_before_worker':result.get('key_down_before_cleanup') is True,
 'worker_saw_unrelated_client':result['cleanup_result']['owner_client_disconnect'].get('reason')=='resource_base_reused_by_unrelated_client' and result['cleanup_result']['owner_client_disconnect'].get('observed_pid')==result['bystander']['pid'],
 'no_cleanup_release_attempt':result['cleanup_result']['owner_release_attempt']=={'reason':'stale_owner_identity','status':'not_attempted'},
 'independent_connection_saw_key_unchanged':result.get('key_down_after_cleanup') is True,
 'operation_remains_unknown_and_denies_replay':result['cleanup_result'].get('status')=='unknown' and result['cleanup_result'].get('release_confirmed') is False and result['cleanup_result'].get('task_success') is None and result['cleanup_result'].get('replay_allowed') is False,
 'harness_restored_private_key':result.get('key_down_after_harness_cleanup') is False,
 'all_child_processes_exited':result.get('owner_exitcode')==0 and result.get('supervisor_exitcode')==0,
 'private_xvfb_cleanup_recorded': 'xvfb_alive_after_cleanup=false' in (root/'preflight.txt').read_text(encoding='utf-8'),
 'inner_runner_exit_zero':(root/'runner.exit').read_text(encoding='utf-8').strip()=='0',
}
report={'schema':'agent-interface/live-xres-bystander-audit-v1','status':'PASS_SCOPED' if all(checks.values()) else 'HOLD_OR_FAIL','checks':checks,'failed':[name for name,value in checks.items() if not value], 'limits':['not public MCP composition','no global input exclusivity proof','no physical desktop/MAP01','no task effect','no hard OS bound','no WSLc','one live Xvfb sample only']}
(root/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,sort_keys=True))
if report['failed']:
    raise SystemExit(1)
