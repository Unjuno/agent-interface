import json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
f=json.loads((p/'FREEZE.json').read_text(encoding='utf-8'))
r=json.loads((p/'RESULT.json').read_text(encoding='utf-8'))
t=(p/'TEST_OUTPUT.txt').read_text(encoding='utf-8')
checks={
 'current_main_controller_blob_is_frozen':f['main_commit']==r['source_main'] and f['controller_git_blob']=='3f43c261e2de0b54cc1e83d2a9d53fd984d70f0a',
 'baseline_skip_case_is_explicit':r['baseline']['future_done_before_wait_condition'] and r['baseline']['queued_typed_observations']==1 and r['baseline']['monitor_calls_before_patch']==0 and r['baseline']['queued_event_skipped_by_outer_loop'],
 'patched_cases_are_tested':r['patched_helper']['tests_passed']==6 and r['patched_helper']['integration_call_order_check'] and r['patched_helper']['completed_future_discard_branch_precedes_eligibility_check'] and all(r['patched_helper'][k] for k in ('hard_crossing_invalidates','queued_terminal_retained','soft_observation_preserves_answer_path','empty_queue_returns_without_wait','arrival_after_snapshot_remains_queued','production_monitor_typed_hard_crossing_invalidates')),
 'test_output_records_historical_five_passes':t.rsplit('Current-main snapshot-boundary extension (2026-10-08):',1)[-1].split('Full controller module import with pinned dependencies',1)[0].count(' ... ok')==5 and 'Ran 5 tests' in t,
 'full_controller_suite_records_six_passes':t.rsplit('Full controller module import after paired-monitor test (2026-10-08):',1)[-1].count(' ... ok')==6 and 'Ran 6 tests' in t,
 'initial_update_audit_failure_preserved':json.loads((p/'AUDIT_UPDATE_INITIAL_FAILURE.json').read_text(encoding='utf-8'))['status']=='FAIL_AUDIT',
 'mainline_retest_is_pinned_and_limited':r['mainline_retest']['controller_git_blob']=='f7b66279d87ebc3704ccef1b6a5ce646611c890b' and r['mainline_retest']['baseline_main_test_git_blob']=='af01126e613c6b1c51e218cab6f199eb56e57efe' and r['mainline_retest']['pr_regression_test_git_blob']=='1ba3950be3b5cb9a6bf4d0e5b5c308a285f0a44b' and 'failed before collection' in t and 'exact drain_pending_observation_events AST' in t and 'Ran 5 tests' in t and r['mainline_retest']['full_controller_imported'] and r['mainline_retest']['dependency_blob_count']==18 and 'Ran 5 tests' in t.rsplit('Full controller module import with pinned dependencies (2026-10-08):',1)[-1],
 'limitations_retained':'No live' in (p/'README.md').read_text(encoding='utf-8') and 'not a measured production race frequency' in f['scope_limits'][0],
}
out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks}
(p/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2));sys.exit(0 if all(checks.values()) else 1)



