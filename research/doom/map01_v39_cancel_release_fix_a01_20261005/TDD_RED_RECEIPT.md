# TDD RED receipt

Before candidate implementation, the two written regression tests ran against the unchanged main-branch v12 owner and v39 bridge and failed on the intended behavior:

- `test_cancel_cleanup_emits_up_receipt_joined_to_admission_context`: expected one `input_release_measurement`, observed zero (`AssertionError: 0 != 1`).
- `test_verified_async_cleanup_reconciles_bridge_held_state`: expected an empty backend held set, observed `{'F8'}`.

These were the two direct failures recorded in the interactive test output before the v13/v2 candidate was written. They are a concise receipt, not a verbatim saved test log.


The first ExecutorV3 integration fixture also stopped before input because it omitted caller-observed focus binding. The exact HOLD construction output is retained in `executor-integration-attempt01.log`; the completed fixture and passing real ExecutorV3 terminal run are in `executor-integration-attempt02.log`.

A third regression reproduced the reviewer-reported reconciliation exception: after the owner recorded a verified cleanup release, the original bridge raised from `input_state` before draining its event log. The new test expected one already-recorded up receipt but observed zero; it passes after draining in `finally`. The pre-fix run was repeated against the original committed candidate bytes and failed with `AssertionError: 0 != 1`.

A fourth regression reproduced the expiry-exit gap: owner `release` completed and recorded a confirmed F8 key-up, then the candidate program raised `Expired` with `lease.cancel` unset. The prior bridge emitted zero up receipts. After unconditional owner-record draining in the execute `finally`, the regression emits one contextual confirmed receipt and clears the bridge-held key. Raw red/green command outputs are `expiry-drain-red.log` and `expiry-drain-green.log`.

A fifth regression exercises expiry through the real `ExecutorV3` and fake-display `InputOwner`: with F8 held, the lease expires, the owner records a confirmed release, and ExecutorV3 reaches an expired terminal without cancellation. The cancellation-gated bridge at commit `518871e9` emitted zero up rows; unconditional execute-exit draining emits exactly one context-bound receipt before the verified-empty terminal. Paired raw outputs are `executor-expiry-red.log` and `executor-expiry-green.log`.

A sixth RED/GREEN pair covers owner-side aggregate reconciliation failures after a sampled per-key up. The regressions inject one `query_pointer()` or aggregate `query_keymap()` failure after the per-key pre/post samples. Against the pre-fix candidate at PR #7805 commit `32686927ce6b07a035beb4c0297171a1f951c6c6`, both tests observed zero drainable up rows (`AssertionError: 0 != 1`). After persisting the per-key rows before aggregate queries, both pass while the partial owner-release record remains `verified=false` and the original query exception propagates. Raw outputs: `aggregate-query-red.log` and `aggregate-query-green.log`.
