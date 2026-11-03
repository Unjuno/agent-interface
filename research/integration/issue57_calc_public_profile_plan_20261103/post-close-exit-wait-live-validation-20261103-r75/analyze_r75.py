#!/usr/bin/env python3
"""Reconcile r75 close order, native lifecycle, artifact and parent effect gates."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ARM=ROOT/'r75-c1'
def read(name): return json.loads((ARM/name).read_text(encoding='utf-8'))
close=read('close.json'); result=read('result.json'); compiled=read('compiled-result.json')
verify=read('verify-task.json'); artifact=read('artifact-read-before-close.json')
lifecycle=close.get('calc_target_lifecycle') or []
life=lifecycle[0] if len(lifecycle)==1 else {}
exit_receipt=life.get('target_process_exit_receipt') or {}
cleanup=life.get('process_group_cleanup') or {}
release=close.get('release') or {}
transitions=compiled.get('method_receipt',{}).get('transitions') or []
exit_ns=exit_receipt.get('observed_monotonic_ns'); release_ns=release.get('monotonic_ns')
gates={
 'preclose_artifact_verified':artifact.get('status')=='verified' and artifact.get('task_success') is True and artifact.get('cells')=={'A1':'731','A2':'864'},
 'both_transitions_released':len(transitions)==2 and all(t.get('release_verified') is True for t in transitions),
 'input_owner_closed_and_released':close.get('status')=='closed' and close.get('verified') is True and close.get('owner_process_retired') is True and close.get('owner_process_exitcode')==0 and close.get('release_confirmed') is True and release.get('verified') is True and release.get('keys_down')==[] and release.get('buttons_down')==[],
 'owner_release_precedes_exact_target_exit':type(release_ns) is int and type(exit_ns) is int and release_ns < exit_ns,
 'exact_target_and_launcher_clean_exit':exit_receipt.get('verified') is True and exit_receipt.get('status')=='exited' and exit_receipt.get('exit_code')==0 and exit_receipt.get('launcher_exit_code')==0 and exit_receipt.get('process_generation')==verify.get('task_effect',{}).get('process_generation'),
 'no_forced_cleanup_needed':cleanup.get('status')=='not_needed' and cleanup.get('clean_exit_verified') is True,
 'parent_task_effect_verified':verify.get('status')=='verified' and verify.get('task_success') is True and verify.get('task_effect',{}).get('parsed_effect',{}).get('cells')=={'A1':'731','A2':'864'} and verify.get('task_effect',{}).get('artifact_sha256')==artifact.get('artifact_sha256'),
 'container_exit_zero':(ARM/'docker-exit-code.txt').read_text().strip()=='docker_exit_code=0'
}
summary={'schema':'agent-interface/post-close-exit-live-validation-analysis-v1','attempt':'r75-c1','status':'PASS' if all(gates.values()) else 'FAIL','gates':gates,'release_to_target_exit_ms':round((exit_ns-release_ns)/1e6,3) if type(exit_ns) is int and type(release_ns) is int else None,'artifact_cells':artifact.get('cells'),'task_success':verify.get('task_success'),'target_exit_code':exit_receipt.get('exit_code'),'launcher_exit_code':exit_receipt.get('launcher_exit_code'),'container_exit_code':0 if gates['container_exit_zero'] else None,'limits':['one fixed Calc task and one fresh generation','no provider/model/API accounting or matched efficiency comparison','does not establish WSLc, MAP01, broad reliability, or overall completion']}
(ROOT/'analysis.json').write_text(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False))
