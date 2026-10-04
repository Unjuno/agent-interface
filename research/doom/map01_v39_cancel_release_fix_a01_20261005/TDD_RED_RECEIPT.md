# TDD RED receipt

Before candidate implementation, the two written regression tests ran against the unchanged main-branch v12 owner and v39 bridge and failed on the intended behavior:

- `test_cancel_cleanup_emits_up_receipt_joined_to_admission_context`: expected one `input_release_measurement`, observed zero (`AssertionError: 0 != 1`).
- `test_verified_async_cleanup_reconciles_bridge_held_state`: expected an empty backend held set, observed `{'F8'}`.

These were the two direct failures recorded in the interactive test output before the v13/v2 candidate was written. They are a concise receipt, not a verbatim saved test log.


The first ExecutorV3 integration fixture also stopped before input because it omitted caller-observed focus binding. The exact HOLD construction output is retained in `executor-integration-attempt01.log`; the completed fixture and passing real ExecutorV3 terminal run are in `executor-integration-attempt02.log`.

A third regression reproduced the reviewer-reported reconciliation exception: after the owner recorded a verified cleanup release, the original bridge raised from `input_state` before draining its event log. The new test expected one already-recorded up receipt but observed zero; it passes after draining in `finally`. The pre-fix run was repeated against the original committed candidate bytes and failed with `AssertionError: 0 != 1`.
