# Issue #6586 — homology vs homotopy representation boundary T0 A01

Status: **`PASS_REPRESENTATION_BOUNDARY_SCOPED`** for the frozen two-obstacle finite algebraic fixture. This separate allocation tests the unverified representation question in Issue #6586 comment #5971584049. It does not rerun the earlier path-class policy experiment or change the #6596/#6602 records.

## H/T/D/C/U

See `PRE_REGISTRATION.md`. The test uses an exact planar embedding with two rectangular obstacles, ordered cut-crossing receipts for complete routes, homology vectors and free-reduced words. It separately includes incomplete/missing/stale evidence controls.

## Scope boundary

The candidate emitted 5,461 complete route receipts for all words through length six. The independent auditor reconstructed the crossings from the polylines, found 77 winding-vector buckets containing multiple reduced homotopy words, and found zero such collisions in 127 one-obstacle words. The empty loop and commutator `abAB` have the same winding vector `(0,0)` but different reduced words. See `REPORT.md` for controls, assumptions, hashes, and interpretation.

No route selection or task-benefit claim is tested. The output is a representation boundary, not a navigation result.
