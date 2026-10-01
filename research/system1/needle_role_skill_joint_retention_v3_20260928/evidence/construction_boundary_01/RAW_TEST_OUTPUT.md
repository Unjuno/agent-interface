# Captured Docker stdout/stderr summary

Exact invocation: see RUN_SOURCE_MANIFEST.json.

```text
Python warning: NumPy unavailable in pinned image (no NumPy-dependent tests used).

12 unittest cases ran in 0.183s.
PASS (9): test_colliding_directories_stop_before_subprocess; test_batch_schedules_and_skill_identity; test_dataset_hash_contract_requires_exact_keys_and_binds_schedule; test_duplicate_batch_mean_loss_control; test_excluded_construction_seed_is_successor_only; test_freeze_sidecar_requires_exact_bare_digest_line; test_fresh_seeds_and_role_conditioned_splits; test_invalid_formal_env_and_seed_stop_before_fit; test_route_receipts_fail_closed_and_bind_adapter_generation_scope.

FAIL (3):
test_logs_are_outside_fresh_empty_runner_output_and_success_receipt_retained — AssertionError: STOP_OUTPUT_NOT_EMPTY != CONSTRUCTION_EXIT_0
test_nonempty_logs_stop_before_subprocess — AssertionError: STOP_OUTPUT_NOT_EMPTY != STOP_LOG_DIR_NOT_EMPTY
test_nonempty_output_stops_before_subprocess — AssertionError: STOP_SOURCE_MISSING != STOP_OUTPUT_NOT_EMPTY

Ran 12 tests in 0.183s
FAILED (failures=3)
Exit code: 1
```

No runner fit/optimizer call was made. This records the first invocation; there was no retry.