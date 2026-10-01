# Issue #6225 T0 preregistration

Allocation: `ROUTE-DIVERSIFICATION-6225-T0-20261002-01`

Intake base: `14b81dd1f6853623a694266b98538f812847257a`

Branch: `research/6225-route-diversification-t0-20261002-01`

## H / T / D / C / U

**H.** On at least one finite task session with an unobservable A-specific regime change and delayed failure detection, a predeclared mixture of two already-qualified same-obligation routes can reduce the session's severe-effect tail versus a best-mean A-first policy with reactive fallback. It need not help when the change is observable, failures are shared, A dominates, B readiness decays, B is unqualified, or route use creates carryover cost.

**T.** Deterministic finite simulator, no model/GUI/input/network. Seven hand-specified cases cross four policies (best-mean reactive, evidence-gated, fixed prospective mixture, oracle diagnostic). The oracle sees latent state and is not deployable. The complete offered session is the unit; task rows are not independent replications. A wrong effect terminates the session; safe noncompletion and not-yet-run obligations remain explicit. A separate enumerator reconstructs schedules, outcomes, carryover and summaries from the fixture. Construction tests compare to hand-calculated expectations and reject nine corruption mutations. Formal candidate and independent audit are each one invocation, in separate pinned network-disabled containers, candidate first and auditor only if candidate exits 0. No retry or output replacement.

**D.** `PASS_METHOD_SCOPED` only if all 28 policy/session rows reconcile to the independent enumerator and hand-calculated controls; all nine corruption controls reject; mixture helps on the hidden A-specific case but shows no safety gain on common-failure and observable-regime controls; all offered tasks, unresolved obligations, and carryover costs reconcile. Any discrepancy is `FAIL_METHOD`; a missing qualified route, complete task frame, or independent scorer is `HOLD`. Infrastructure/ownership failure before invocation is `STOP_NOT_EVALUATED`, not scientific FAIL.

**C.** Deterministic tables, policy schedules, finite horizons, regime labels, and carryover rules are constructed rather than sampled. The examples prove only that this finite method can distinguish a planted hidden-shock contrast from specified controls. The oracle is an unattainable upper bound. Queue penalty is explicitly modeled as route-induced carryover into the next task.

**U.** No empirical route qualification, GUI correctness, real session survival, population probability, algorithmic novelty, or live policy recommendation. No randomization on consequential tasks. T1 requires same-obligation route qualification, independent effect/collateral oracle, complete session IDs, detection-delay evidence, qualified resets and an explicit isolated-versus-shared estimand.

## Freeze and run order

Frozen inputs are `fixture.json`, `candidate.py`, `audit.py`, and `test_method.py`; their SHA-256 values are in `SHA256SUMS`. Run construction tests before formal freeze. At formal start, recheck main, Issue #6225, branch/PR conflicts, queue owner release, Docker context/image digest/platform, running-container inventory, source hashes and empty output path. If any shared container remains without explicit owner release or an exact assignment is absent, retain `STOP_NOT_EVALUATED`; do not inspect or alter that container. A formal run under this terminal pre-candidate STOP is prohibited; a granted follow-up must use a new allocation, branch/path and current-main refreeze. Candidate and raw-only auditor must then each run once in separate `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` Linux/arm64 containers, `--network none`, bounded CPU/memory/PIDs, read-only source and isolated output. Preserve all outputs/exits; never retry an allocation.
