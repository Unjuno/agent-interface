# Issue #6586 representation-boundary T0 — A01

Allocation `HOMOLOGY-HOMOTOPY-6586-T0-20261007-A01`; source `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`; additive path `research/analysis/homology_vs_homotopy_6586_t0_20261007/`. This is a fresh experiment on the distinct unverified representation proposal in Issue #6586 comment #5971584049, not a rerun or regrading of #6596/#6602 and not a navigation-policy experiment.

## H / T / D / C / U

**H.** For two disjoint planar obstacles and based complete routes, the per-obstacle signed crossing/winding vector can be equal for routes with different homotopy classes, because abelianization forgets crossing order. An order-preserving reduced generator word retains the distinction. For one obstacle (free group rank one), this particular noncommutative collision is unavailable.

**T.** Freeze two rectangular obstacles, their upward cut rays, exact integer-coordinate generator loops and common basepoint-to-goal tail. Reconstruct the ordered crossing receipt from the complete polyline; independently compute (i) the abelianized exponent vector and (ii) the freely reduced word. Exhaust every word over `{a,A,b,B}` through length six (5,461 routes), plus every one-generator word through length six (127 routes). Include identity/commutator, adjacent inverse cancellation, equal reduced word with unequal raw lengths, incomplete prefix, missing receipt, and changed-topology controls. The full group-theory statement is also derived in the report; the finite computation is an implementation check, not a proof of the theorem.

**D.** `PASS_REPRESENTATION_BOUNDARY_SCOPED` only if the independent raw-only auditor reconstructs every crossing sequence from obstacle-avoiding planar polylines, recovers the commutator/identity equal-vector but distinct-reduced-word witness, validates inverse cancellation and same-word controls, finds no bounded rank-one collision, returns UNKNOWN for incomplete/missing/stale evidence, and rejects all frozen mutations. Any geometry intersection or row mismatch is FAIL without retry.

**C.** For two punctures the based fundamental group is the free group `F2`; first homology is its abelianization `Z²`. The commutator `abAB` maps to `(0,0)` but is freely reduced and nonidentity. For one puncture `F1` is cyclic/abelian, so the exponent vector suffices. These are standard algebraic facts; the code checks the concrete route receipt and bounded enumerator only.

**U.** No visual sensor, map reconstruction, route policy, agent behavior, GUI/game, task progress, safety, release, timing, or application effect is tested. A source-visible two-cut ordered crossing receipt is assumed. Wrong or missing perception is represented only by explicit UNKNOWN controls. This result cannot license use of scorer-only topology in a controller.

## Frozen execution

- Official `python:3.13-alpine` image by digest; OrbStack isolated CPU container, no network, read-only source mount, 512 MiB requested, one CPU.
- Candidate and independent auditor each run once after freeze; zero retries.
- Construction unit tests are pre-freeze. Formal candidate emits all rows and summaries; independent auditor reads saved raw bytes and frozen fixture only, without importing candidate code.
- No external source or service is queried from the container. No product runtime, GUI, model, credentials, or live authority is used.
