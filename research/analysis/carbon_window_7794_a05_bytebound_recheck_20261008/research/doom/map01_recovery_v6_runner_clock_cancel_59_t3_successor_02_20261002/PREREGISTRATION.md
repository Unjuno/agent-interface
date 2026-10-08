# T3U preregistration — one shared monotonic clock domain

Allocation: `MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3U-20261002-01`  
Issue: #6252; parent #59; successor to #6242/T3S STOP, not a candidate retry.  
Base: `97afcb82f90616589801a256893f886010ed6d27`  
Branch: `research/6252-v6-runner-shared-clock-t3u-20261002`  
Path: `research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_02_20261002/`

## H / T / D / C / U

**H — hypothesis.** The exact v6 `_run_arm` with an exact Executor-v10 and exact Lease implementation, all sampling one injected monotonic clock, retains fallback activity during synchronous clock delay when lease-valid; otherwise the lease itself expires/releases before return and the runner's late cancel does not match. The runner's stored planner end equals the exact returned clock sample.

**T — test.** Host CPU, no external effects. Load exact v6, executor-v10, and Lease Git objects from the pinned main SHA. Provide one `Clock.now_ns()` source to `Session.runtime_clock`, timer receipts, release/cancel timestamps, and exact Lease constructor's clock argument. Preserve exact Lease implementation; only inject its documented clock callable at the Executor's Lease constructor seam. On the delayed runtime-clock call, sleep, sample once into a local, store it, and return that same integer. Construction-only `_run_arm` smoke once at 30 ms plus binding/cancel/release gates. Only after construction and seven mutation tests pass, freeze sources/code/gates and push. Then run one candidate containing exactly A=(timer 600 ms, clock delay 400 ms, lease 2,000 ms) and B=(600, 1,600, 1,500 ms); one separate raw-only audit if candidate exits 0; no retries.

**D — decision.** `PASS_RUNNER_CLOCK_DELAY_SCOPED` only if source/candidate/auditor/test hashes match; two exact cases and one invocation/no retries; for A, `planner_end_ns == clock_return_ns`, matched cancellation is observed, and verified release is 350–2,000 ms after timer expiry and within 50 ms after clock return and cancel observation; for B, verified release is within 50 ms of `planner_start_ns + 1,500 ms`, before clock return, with no cancel observation and a recorded unmatched late cancel; independent auditor reconstructs source order/timing/receipts with zero errors. Else preserve exact FAIL/HOLD/STOP and do not retry or change thresholds.

**C — constraints.** This fake session/backend exercises Python runner control flow; it has no OS subprocess or real pipe. A shared monotonic source aligns timestamps and Lease deadlines but cannot establish transport scheduling or natural latency frequency. Docker is not used: #5085 records an active queue/owner reservation and does not provide this allocation a lease; host CPU has no external effect.

**U — unverified.** No formal/live MAP01 allocation, gameplay, threat response, physical input occupancy, safety/efficacy, human tempo, or product claim. This does not close #59's live threat-exposure gate.

## Frozen command and no-retry rule

After publishing the hash freeze and recording it on #6252, run exactly once:

`python3 research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_02_20261002/run_experiment.py`

If candidate exits zero, run exactly once:

`python3 research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_02_20261002/audit_trace.py --raw research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_02_20261002/results/raw_trace.json --out research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_02_20261002/results/audit.json`

Construction and mutation-test runs are preparation gates, not formal result rows or candidate invocations.
