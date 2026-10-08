# Lease cancellation acknowledgement contract — host construction T0

## Lineage and separation

Issue #6228 records a consumed candidate/auditor allocation that stopped as `STOP_HARNESS_CANCEL_NONCOOPERATIVE`: its fake backend called `Lease.wait()` but ignored a `True` cancellation return, so its A and C cases ran to lease expiry. Preserve that first outcome unchanged. This is a new, CPU-only contract test of the real current-main `Lease` primitive, not a rerun of #6228's clock-delay scenarios and not a timing/effect experiment. The question is whether a bounded adapter contract can distinguish correct cancellation cooperation from the exact ignored-return defect before a higher-level timing experiment.

## H / T / D / C / U

**H.** Given the actual `research/live_control/lease.py` implementation, an independent contract oracle can distinguish (a) a worker that checks the boolean returned by `Lease.wait()` and terminates on `True` from (b) a worker that ignores `True` and repeats until lease expiry. The contract should accept the former, reject the latter and reject expiry mislabeled as cancellation.

**T.** Freeze current-main commit and the real Lease source blob/SHA-256. Use a fake monotonic clock and a real `threading.Event` from the actual `Lease` class. Drive three deterministic schedules: cancel before deadline, no cancel until deadline, and cancel observed immediately before deadline. Candidate rows record wait return/exception, worker terminal label, cancellation state, deadline, and step count. A separately written raw-only auditor reconstructs the expected outcomes from the frozen schedule and raw rows. Mutation tests alter cancel return handling, terminal labels, deadline relation, and event order. No Docker, GUI, model, GPU, external input, network in candidate, or live allocation. This narrow lease-contract test is host-local by design; it does not reproduce the original clock-RPC delay scenarios.

**D.** `PASS_LEASE_CANCEL_ACK_CONTRACT_SCOPED` only if the actual Lease returns `True` for pre-deadline cancellation and the cooperative worker terminates as cancelled before deadline; the no-cancel worker terminates as expired at/after deadline; the boundary schedule is classified from the actual Lease behavior without mislabeling; the independent auditor agrees with all rows; and all declared mutations are rejected. Any mismatch is a retained FAIL/STOP, with no retry.

**C.** Passing establishes that the Lease primitive exposes a cancellation acknowledgement and that this consumer contract can catch ignoring it under the deterministic host schedule. The earlier #6228 result then remains a harness defect requiring a separately preregistered successor; this package does not repair/re-execute it and says nothing about production RPC ordering or MAP01 release latency.

**U.** A synthetic clock and worker schedule are not OS scheduling or real executor transport. The test cannot establish the synchronous runtime_clock delay effect, cancellation latency distribution, formal runner behavior, physical input release, game outcome, or safety. Authority/freshness/effect rules are outside this contract.

## Freeze

- Allocation: `LEASE-CANCEL-ACK-CONTRACT-HOST-T0-20261002-01`.
- Base: current-main `4cf0a3dfde1219671b671bf0a9079a11dcb2e159`.
- Source: exact bytes extracted from current-main `research/live_control/lease.py`, Git blob `b9dac6bb4063928354733d79bf371909a288a3d1`, SHA-256 `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f`, retained as `frozen_lease_source.py`.
- Candidate invocation: exactly one. Auditor invocation: exactly one, only after candidate exit 0. Retries: zero.
- Container: not used. Docker Desktop service is Stopped/Manual and Docker Engine inventory queries are unresponsive; no service/process/container changed.

## Predeclared schedules

1. **cancel-before-deadline:** start at 100 ns, deadline 1000 ns, cancel after first timed wait, advance fake time to 200 ns, then wait again. A cooperative consumer exits `cancelled`; an ignoring consumer must not be accepted.
2. **deadline-without-cancel:** start at 100 ns, deadline 1000 ns, advance fake time to 1000 ns before wait. Actual `Lease.wait()` raises `Expired`; terminal is `expired`.
3. **cancel-at-boundary:** `Lease.wait()` checks the deadline before waiting. At exactly 1000 ns it raises `Expired`, even if the event was set at that instant; the contract must not label this as an observed pre-deadline cancellation acknowledgement.

The harness uses a frozen fake clock for `Lease.check()` and a zero-timeout real Event wait, with explicit clock advancement between calls; it does not sleep to simulate time. The candidate log retains call/return order. The independent auditor consumes raw JSONL only and does not import candidate helpers.

## Integrity and run discipline

All candidate/auditor/test source files and this plan are hashed in `FREEZE.json` before candidate invocation. First raw outcome is stored only under `results/host-t0-01/`; candidate refuses an existing output path. No post-result source changes or candidate/auditor reruns are permitted. A separate correction requires a new allocation/path.
