# Preregistration: v6 runner clock/cancel successor

Allocation: `MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3S-20261002-01`  
Parent: #59; successor to #6242, preserving #6242/#6244 evidence unchanged.  
Base: `279679a33f6029c6e13eca6be51890d8bebb25e7`  
Branch: `research/6242-v6-runner-clock-cancel-t3s-20261002`  
Path: `research/doom/map01_recovery_v6_runner_clock_cancel_59_t3_successor_01_20261002/`

## H / T / D / C / U

**H — hypothesis.** The exact frozen v6 `_run_arm` closure, when its synchronous `runtime_clock()` is delayed after the planner timer, leaves the cooperative fallback active until clock return and subsequent cancel if the lease remains valid. If the lease expires first, exact executor-v10/Lease releases at the deadline and the later cancel is unmatched.

**T — test.** Invoke the exact v6 `_run_arm` source compiled from the pinned main Git object, with a deterministic fake session/backend and the exact executor-v10 and Lease Git objects. Construction smoke once at 30 ms. Then one candidate invocation with exactly two scenarios: A: planner wait 600 ms, clock delay 400 ms, lease 2,000 ms; B: planner wait 600 ms, clock delay 1,600 ms, lease 1,500 ms. No real input, game, GUI, model, GPU, or network. Use host CPU because Docker Desktop/shared slot release is unavailable; do not start the shared engine.

**D — decision gates.** `PASS_RUNNER_CLOCK_DELAY_SCOPED` only when frozen source identity and preregistered hashes match; exactly the two cases and one invocation/no retries are present; A's planner end equals clock return, cancel matches and is observed, and verified release occurs 350–2,000 ms after timer expiry and within 50 ms after clock return/cancel; B's verified release occurs within 50 ms of its 1,500 ms lease deadline before clock return, and late cancel is unmatched/not observed; independent raw-only audit reconstructs ordering and all receipts with zero errors. Otherwise retain typed FAIL/HOLD/STOP; no threshold changes after freeze.

**C — constraints.** MockSession is neither an OS subprocess nor real pipe; fake telemetry supplies receipts. This exercises actual v6 Python control flow and exact Executor/Lease but does not measure transport scheduling or natural RPC latency.

**U — unverified.** No formal/live MAP01 allocation and no gameplay, safety, efficacy, physical key occupancy, human-tempo, or product claim.

## Frozen procedure

1. Run pre-freeze tests and one construction smoke before freezing.
2. Publish exact candidate/auditor/tests/preregistration hashes and source blob identities, then freeze in `FREEZE.json` and commit/push.
3. Post this preregistration and commit/hash manifest to #6242 before candidate invocation.
4. Run `python3 <path>/run_experiment.py` exactly once. If it fails, preserve raw state and stop; do not retry.
5. If candidate exits zero, run `audit_trace.py` exactly once against the raw JSON. No changes to gates or frozen code.

Environment intended: macOS ARM64, CPython 3.14.5, host CPU, no container; one candidate run and one independent audit; retries zero.
