import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
raw=Path('research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl')
freeze=(root/'FREEZE.md').read_text(encoding='utf-8-sig')
run=json.loads((root/'RUN.json').read_text(encoding='utf-8-sig'))
candidate=json.loads((root/'CANDIDATE_RESULT.json').read_text(encoding='utf-8'))
primary=json.loads((root/'AUDIT.json').read_text(encoding='utf-8'))
negative=json.loads((root/'NEGATIVE_CONTROL.json').read_text(encoding='utf-8'))
raw_text=(root/'RAW_TEST.txt').read_text(encoding='utf-8-sig')
container=(root/'CONTAINER_SNAPSHOT.txt').read_text(encoding='utf-8-sig')
result_text=(root/'RESULT.md').read_text(encoding='utf-8')
checks={
 'pass_exit_zero':run.get('result')=='PASS' and run.get('exit_code')==0,
 'source_hash_bound':hashlib.sha256(raw.read_bytes()).hexdigest()==candidate.get('source_events_sha256') and hashlib.sha256(raw.read_bytes()).hexdigest() in freeze,
 'one_static_sixteen_step_program':candidate['accepted_program']['count']==1 and candidate['accepted_program']['step_count']==16,
 'health_change_and_span':candidate['preceding_sample']['health']==61 and candidate['cover_samples']['first']['health']==55 and candidate['cover_samples']['last']['health']==48 and candidate['cover_samples']['count']==52,
 'sample_window_and_cancel_order':candidate['response_order']['first_lower_health_capture_ns']==candidate['cover_samples']['first']['capture_ns'] and candidate['response_order']['cancel_requests'][0]['requested_ns']>candidate['cover_samples']['last']['capture_ns'],
 'steps_continue_before_cancel':candidate['execution']['started_steps']==list(range(12)) and candidate['execution']['completed_steps']==list(range(11)),
 'primary_audit_passes':primary.get('pass') is True and all(primary['checks'].values()),
 'mutation_control_rejected':negative.get('pass') is False and negative['checks']['cover_health_decreases_55_to_48'] is False and 'NEGATIVE_CONTROL_REJECTED' in raw_text,
 'verified_release_then_terminal':candidate['response_order']['terminal'][0]['release_verified'] is True and candidate['response_order']['terminal'][0]['status']=='cancelled',
 'swap_limit_warning_retained':'does not support swap limit capabilities' in raw_text,
 'no_container_left_running':'Up ' not in container,
 'all_executed_sources_hash_pinned':all(hashlib.sha256((root/name).read_bytes()).hexdigest() in freeze for name in ('candidate.py','auditor.py','run_a02.sh')),
 'result_scope_limits_present':'does not establish' in result_text and 'does not authorize such a run' in result_text,
}
out={'schema':'v39-static-cover-health-posthoc-package-audit-a02-v1','pass':all(checks.values()),'checks':checks}
(root/'PACKAGE_AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
