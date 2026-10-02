# Issue #6147 T0 A04 — post-probe state/effect qualification

Allocation `AI-6147-T0-20261003-04` is a fresh successor to A03's qualified
`FAIL_AUDIT_CONTROL_COVERAGE`. A03 remains unchanged and neither its candidate
nor auditor output is reused. Base main: `43f7cd88d91af05036fae2100ec4e155c59e105c`.
Additive artifacts only. Issue scope is analytical/no-model; use host CPython
standard library, no OrbStack/container, model, GUI, network, or physical input.

## H / T / D / C / U

**H.** Under a declared finite deterministic machine, safe adaptive probes can
separate action-relevant terminal states when evidence differs, but initial
state identification alone does not authorize a later action. A probe sequence
may invalidate the old target/action envelope; conversely, distinct initial
states may converge to one current safe action-equivalent terminal state
without identifying which initial state occurred. Safe-bisimilar
action-different states remain `YIELD`; an unsafe informative action is never
admitted.

**T.** Four new deterministic hypothesis pairs, disjoint from A03's raw:
(1) `p→q` distinguishes initial A/B by LEFT/RIGHT while both terminal states
invalidate the formerly permitted target action; (2) safe `p` leaves initial
C/D observationally aliased but converges them to one terminal Z with one
declared safe effect envelope; (3) action-equivalent aliased states resolve
without a probe or initial identity claim; (4) action-different E/F states have
an exact safe-output-invariant relation while unsafe `u` distinguishes them.
Enumerate all complete safe output-contingent trees to depth 2, and retain
terminal reachable-state/effect envelopes and terminal decision status at every
leaf. A separately implemented raw-only auditor independently reconstructs
tables, tree sets/counts/digests, fixed-word bounds and relation closure. It
must explicitly inject and reject an unsafe-`u` policy, a dropped branch, a
fabricated singleton, a stale initial-envelope action after p→q, a false
convergence/terminal-effect claim, a non-closed relation, and same-image
recapture-as-identification. One candidate call then one auditor call, once
each. Any failure is preserved; no retries/tuning.

**D.** `PASS_METHOD_SCOPED` only if all enumerated trees and selected policies
match; A/B are distinguished by minimum safe depth 2 but terminal effect remains
denied; C/D converge to terminal Z and permit only the declared current action
without claiming initial identity; action-equivalent aliases stop without
probing; E/F yield under the exact closed relation; unsafe `u` is proved
informative but excluded and the mutated policy is rejected; and every frozen
mutation control rejects. Missing terminal-state/envelope coverage or any
audit/control mismatch is `FAIL_AUDIT`/STOP, never PASS.

**C.** The declared model may omit the real application state or misstate probe
effects. Typed effect receipts or ordinary reobservation/YIELD may be safer.
Model-relative convergence/identity does not establish real authority.

**U.** Finite deterministic authored fixtures only. No GUI, state completeness,
probe safety, reset validity, external-effect truth, application transfer,
authority, runtime, or product claim.

## Freeze and run protocol

Construction/syntax checks occur before source freeze and are not formal
results. Freeze source hashes, interpreter identity, base main, UTC timestamp,
empty output path and exact commands in `FREEZE.md`. After that, no edits to
candidate/auditor or fixture. Candidate runs once and writes unique `RAW.json`;
only on exit 0 run the separate auditor once. Preserve stdout/stderr/status and
hashes. Applicable local repository CI and checksums follow the formal run;
never represent them as additional experiment invocations.
