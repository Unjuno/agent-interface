# Preregistration — Issue #6549 supported-class finite frontier

Allocation: `PRIVACY-DISCOVERY-SUPPORTED-CLASSES-6549-T0-20261002-01`
Issue: https://github.com/Unjuno/agent-interface/issues/6549
Frozen base: `60e2e7bb8a69cb7270fc2082e0affc5bf2789876`
Scope: deterministic finite synthetic accounting comparison only. No real data, deployed privacy mechanism, DP guarantee, telemetry collection, or cohort-risk claim.

## H / T / D / C / U

**H.** Under bounded one-report-per-client synthetic cohorts, exact released counts are a useful unattainable upper bound, while a thresholded report with explicit `UNKNOWN` and a bounded-noise count can retain supported rare-class visibility. For an exact singleton label under user-level `(epsilon=1, delta=0)` DP, the conditional Dwork–Roth inequality fixes the worst-case detection/false-report frontier; for classes with two or more independent bounded contributors, finite-cohort discoverability may remain possible. Correlated clients, duplicate reports, or ambiguous taxonomy must widen support or return `UNKNOWN` rather than silently claim absence.

**T.** Exhaustively enumerate eight frozen ten-client count histograms from `fixture.json`: common class, two supported rare classes, singleton severe mode, taxonomy merge/split, unknown client independence, duplicate-client report, and no-failure control. Compare (1) local exact-only, (2) exact aggregate upper bound (explicitly NON_PRIVATE), (3) threshold `k=2` with suppressed=`UNKNOWN`, and (4) clipped per-client count plus deterministic bounded-noise sensitivity sweep `eta∈{0,1,2}`. For every exact-label singleton, independently check `P(report|present) <= exp(epsilon)*P(report|absent)+delta` using a separately coded deterministic threshold frontier—not randomized empirical estimates. This is not a proof that arm 4 is DP: it only computes an assumed additive-noise release under the stated sensitivity and does not bound its privacy loss.

**D.** `PASS_METHOD_SCOPED` iff all rows are independently reconstructed; the exact non-private arm is always labeled non-private; every threshold/noise suppression is `UNKNOWN`, never ABSENT; common positive and no-failure controls are correct; the singleton analytical bound is reproduced for all enumerated false-report probabilities; and all frozen mutation controls are rejected. A violation is `FAIL_METHOD`. The H frontier is descriptive only: no privacy-qualified utility claim is allowed unless an actual mechanism's guarantee is separately established.

**C.** Larger cohorts or coarser predeclared categories may retain useful discovery; local-only adjudication plus voluntary case escalation may dominate aggregate release. Taxonomy quality may dominate noise.

**U.** The model omits composition, side channels, malicious clients beyond the one duplicate fixture, realistic data dependence, adaptive vocabularies, severity-weighted decisions, participation leakage and repeated releases. A configured noise scale alone is not a DP certificate.

## Frozen verification / stop rules

Construction tests must pass before formal use. Then one candidate invocation and one independent auditor invocation, each at most once; no retries or tuning. Raw candidate bytes, stdout/stderr, exit codes, hashes, and audit are retained. Any source/fixture/hash mismatch stops before scoring. No GitHub issue/PR write occurs until results are preserved and locally checked. Eligible single-container CPU execution uses the repository-default WSLc where available; no OrbStack state is required by this deterministic fixture.
