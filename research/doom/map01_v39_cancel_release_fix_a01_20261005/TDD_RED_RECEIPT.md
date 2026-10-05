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

A seventh RED/GREEN pair composes those owner-query faults through current-main ExecutorV12 expiry. Against pre-fix candidate commit `32686927ce6b07a035beb4c0297171a1f951c6c6`, both integrations reached terminal without the required `reason=expired` per-key receipt (`AssertionError: 0 != 1`). With the fix, both emit one confirmed contextual expiry-up before the later verified-empty terminal barrier. Raw output: `executor-v12-query-fault-red.log` and `executor-v12-query-fault-green.log`.

A deterministic post-drain schedule and a duplicate-up classification regression were added for A08. The prior bridge fails the post-drain case with zero published up receipts before the terminal and labels the NOOP as a second `input_release_measurement`. Candidate green runs close the release barrier and publish one confirmed, actuation-bound up; the later up is retained as `input_release_noop`. See the paired `post-drain-*` and `noop-row-*` logs. The focused suite includes both cases; all testing remains fake-display only.


The reviewer-requested focus-invalidation lifecycle case is retained in `focus-drain-red-current.log` and `focus-drain-green-current.log`. With a fake observed focus change, the old bridge reaches a needs-decision terminal without publishing the already-started owner key-up; the candidate's release barrier drains one contextual `focus_changed` receipt first.


A10 RED/GREEN rebases the confirmed-owner-hold retirement repair from #7823 onto #7805 head `61502e45d40b67b6d588b4e8357e42fde05a9dbe`. The baseline confirms F8 up and retains the partial unverified owner-release record, but after the aggregate keymap fault it accepts/injects a second key request under the same lease. The repair removes the owner-held entry at the confirmed per-key up, stores the aggregate exception as an owner fault, clears the active lease, and rejects the second request before injection. Logs: `owner-ledger-retirement-red.log` and `owner-ledger-retirement-green.log`.


## A11 — ambiguous receipt-sink failure is terminal evidence loss

**H:** On exact #7805 head `e00c7f5e5c949095d40ade458355e55ea5990b9d`, the bridge advances its owner-record cursor before iterating per-key rows. If the sink appends a row and then raises, it is unknown whether that row persisted; silently advancing can lose later rows, while retry can duplicate the accepted row.

**T:** Admit F8 and F9 on the fake display, let the owner release both, then make the emitter append each release row and raise after appending F9. The RED loads the unmodified bridge blob `9028c652d2134b3f748b99069069748e1aef2cdf`. The candidate stores a sticky publication fault before propagating the exception.

**D:** PASS requires the first drain to propagate the sink error, later drains to fail closed without re-emitting either row, the bridge to retain F9 conservatively, and any new down to be rejected before injection. The baseline silently accepts the second drain after its cursor has skipped the record; candidate GREEN passes.

**C:** The earlier #7805 probe raised before appending its second row and already established the lost-later-row case. This A11 schedule tests the distinct append-then-raise ambiguity; it does not assume an idempotent sink. PR #7836 separately explores pending record indices and per-row deduplication, but does not resolve whether a sink accepted a row before throwing.

**U:** Bundled CPython 3.12.14 on macOS arm64; fake display and in-memory emitter only. This is a candidate evidence-loss STOP policy, not durable-storage fault-injection, real X11, live input, production wiring, task effect, useful feedback, recovery, gameplay, latency, or live MAP01 evidence.
