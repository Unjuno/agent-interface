from pathlib import Path
import json,re
root=Path(__file__).parent
c=json.loads((root/'CONDITIONS.json').read_text(encoding='utf-8'))
r=json.loads((root/'result.json').read_text(encoding='utf-8'))
stdout=(root/'stdout.txt').read_text(encoding='utf-8')
after=(root/'xvfb-after-run.txt').read_text(encoding='utf-8')
match=re.search(r'Ran 1 test in ([0-9.]+)s',stdout)
recovery=r['recovery']
stale=r['stale_alias_after_recovery']['result']
stale_gen=r['stale_generation']
oracle=r['post_recovery_task_oracle']
binding=r['observe']['source']['pointer_binding']
checks={
 'one_unittest_passed':bool(match) and '\nOK\n' in stdout and (root/'exit-code.txt').read_text().strip()=='0',
 'scoped_result_status':r['status']=='PASS_SCOPED_XVFB_STANDARD_CALLER_RECOVERY',
 'xvfb_identity_captured':r['xvfb']['status']=='captured' and r['xvfb']['package_stdout']=='xvfb='+c['environment']['xvfb'],
 'standard_observation_and_identity_enabled':r['observe']['status']=='observed' and r['observe']['session']['process_identity'] and r['observe']['session']['query_worker'] and r['observe']['session']['window_lifecycle'],
 'process_and_window_generations_bound':bool(re.fullmatch('[0-9a-f]{64}',binding['process_generation'])) and bool(re.fullmatch('[0-9a-f]{64}',binding['window_generation'])),
 'recovery_release_verified_and_bounded':recovery['result']['status']=='input_recovered' and recovery['result']['release']['verified'] and 0<=r['recovery_elapsed_ms']<3000,
 'independent_recovery_key_readback_up':r['independent_recovery_readback']['reader_connection']=='independent X client' and r['independent_recovery_readback']['keycode_b_down'] is False,
 'recovery_requires_review_and_denies_replay':recovery['result']['review_required'] and recovery['result']['replay_allowed'] is False and recovery['task_success_api'] is None and r['recovery_review']['status']=='reviewed',
 'stale_alias_refused_before_dispatch':stale['status']=='refused' and stale['input_dispatched'] is False and not r['stale_alias_after_recovery']['replay_allowed'],
 'post_recovery_independent_effect_and_release':oracle['reader_connection']=='independent X client' and oracle['observed_property_value']==oracle['expected_property_value']==[3] and oracle['key_press_then_release'] is True and oracle['runtime_task_success_api'] is None,
 'destroyed_target_generation_refused':stale_gen['result']['status']=='refused' and stale_gen['result']['result']['input_dispatched'] is False and stale_gen['target_queries_retired'] is True and stale_gen['review_required'] is True,
 'server_close_releases_and_verifies':r['close']['status']=='closed' and r['close']['verified'] and r['close']['release_confirmed'] and r['close']['release']['verified'] and r['close']['release']['keys_down']==[] and r['close']['release']['buttons_down']==[],
 'private_xvfb_stopped':f"private_xvfb_pid={r['xvfb']['pid']} state=absent" in after,
}
summary={'run_id':c['run_id'],'decision':'PASS_SCOPED_NATIVE_WSL_XVFB_TARGET_GENERATION_RECOVERY' if all(checks.values()) else 'FAIL_OR_INCOMPLETE','checks':checks,'derived':{'test_runtime_seconds':float(match.group(1)) if match else None,'recovery_elapsed_ms':r['recovery_elapsed_ms'],'recovery_effect_latency_ms':r['recovery_app_effect']['call_start_to_effect_commit_ms'],'post_recovery_effect_latency_ms':oracle['call_start_to_effect_commit_ms'],'post_recovery_effect':oracle['observed_property_value'],'runtime_task_success_api':oracle['runtime_task_success_api']},'qualification':'One native WSL/Xvfb test only. Synthetic task oracle is independent of the runtime API. Does not establish physical input, MAP01, general-purpose recovery, population reliability, or matched efficiency; no WSLc/Docker allocation was used.'}
(root/'audit.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
print(summary['decision'])
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(json.dumps(summary['derived'],sort_keys=True))
