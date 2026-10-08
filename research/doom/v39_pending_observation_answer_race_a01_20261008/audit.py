import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
f=json.loads((p/'FREEZE.json').read_text(encoding='utf-8'))
r=json.loads((p/'RESULT.json').read_text(encoding='utf-8'))
t=(p/'TEST_OUTPUT.txt').read_text(encoding='utf-8')
checks={
 'current_main_controller_blob_is_frozen':f['main_commit']==r['source_main'] and f['controller_git_blob']=='3f43c261e2de0b54cc1e83d2a9d53fd984d70f0a',
 'baseline_skip_case_is_explicit':r['baseline']['future_done_before_wait_condition'] and r['baseline']['queued_typed_observations']==1 and r['baseline']['monitor_calls_before_patch']==0 and r['baseline']['queued_event_skipped_by_outer_loop'],
 'patched_cases_are_tested':r['patched_helper']['tests_passed']==3 and all(r['patched_helper'][k] for k in ('hard_crossing_invalidates','queued_terminal_retained','soft_observation_preserves_answer_path','empty_queue_returns_without_wait')),
 'test_output_records_all_three_passes':t.count(' ... ok')==3 and 'OK' in t,
 'limitations_retained':'No live' in (p/'README.md').read_text(encoding='utf-8') and 'not a measured production race frequency' in f['scope_limits'][0],
}
out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
(p/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2));sys.exit(0 if all(checks.values()) else 1)

