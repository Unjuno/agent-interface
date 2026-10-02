# Issue #43 AoII measurement-method T0

## H/T/D/C/U

- **H:** For a finite source/receiver trace with explicit predicate truth and explicitly reported receiver belief, wall-clock age alone can rank two delivery policies as equal or preferable while the time-integral of confident predicate error ranks them differently. The proposed incorrect-belief-age (AoII) measure can expose that inversion without granting any runtime authority.
- **T:** Against current-main `bd9c4c5ceca68f4dc09bb39d27b140a987b68656`, use one host-only, standard-library deterministic trace. Freeze cases: old-but-unchanged, recent-but-superseded, short-lived critical transition, rapid reversal (A→B→A) with two explicitly different receiver beliefs at the same decision tick, incomplete/missing truth, and source-generation change. Candidate emits the trace and declared per-delivery AoI/AoII; a separately written raw-only auditor reconstructs source truth from literal events, checks the independently supplied decision belief, and verifies all rows and fixed corruptions. One candidate invocation and one separate audit invocation; no retry/tuning. This is a method-identifiability test, not a policy-efficacy comparison.
- **D:** `PASS_METHOD_SCOPED` iff the byte-frozen auditor reconstructs every tick; old-but-unchanged has higher AoI but zero AoII while newer-but-superseded has lower AoI and positive AoII; rapid reversal is scored only when the explicit receiver belief is wrong; missing truth yields UNKNOWN; generation mismatch cannot be labeled current; and all frozen mutation tests reject. `FAIL_METHOD_SCOPED` if the declared estimator misses those distinctions. `STOP_AUDIT_SOURCE_DRIFT` if auditor bytes change after freeze; a later corrected supplemental replay cannot repair the allocation. `HOLD_UNOBSERVABLE` if truth, belief, or delivery timing is absent/ambiguous. This is a method-identifiability result, not policy efficacy.
- **C:** AoI plus critical-edge retention and generation checks may already capture all actionable cases; a separate AoII metric may add no decision-relevant signal.
- **U:** Hand-authored finite traces do not establish GUI semantic truth, planner beliefs, natural prevalence, reduced errors, token/latency gains, or runtime utility. The metric is offline and cannot be an online authority signal.

## Freeze

> Post-execution addendum: this document was amended after the candidate/audit sequence to record the observed `STOP_AUDIT_SOURCE_DRIFT` condition. The exact pre-execution document SHA-256 remains in `FREEZE.json`; this addendum does not replace that frozen copy or authorize another run.

- Issue: [#43](https://github.com/Unjuno/agent-interface/issues/43), candidate refinement comment #5925881944 (explicitly unverified / no experiment run).
- Main: `bd9c4c5ceca68f4dc09bb39d27b140a987b68656`.
- Additive evidence path: `research/analysis/aoii_observation_freshness_43_t0_v1/`.
- Host: macOS arm64, CPython 3.14.5, standard library only; no Docker/OrbStack, model, GUI, input, network, user data, or runtime authority.
- Candidate/auditor commands and source hashes are frozen in `FREEZE.json` after files are written and before execution; result is strictly construction/method T0.
