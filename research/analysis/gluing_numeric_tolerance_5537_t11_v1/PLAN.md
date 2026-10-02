# Issue #5537 T11 — derive approximate-section status from numeric evidence

## H / T / D / C / U

**H.** Given noisy local numeric relations rather than a manually supplied status/spread tag, exhaustive finite optimization can derive the minimum worst-case local residual. The action gate should then reject when the minimax residual exceeds tolerance and apply the T10 contract policy only to genuine within-tolerance approximate sections.

**T.** Freeze three-variable quarter-grid values represented in eighth-units `{0,2,4,6,8}` and relation cycles with target offsets: exact `(0,0,0)`, near-inconsistent `(0,0,4)`, and larger-inconsistency `(0,0,8)`. Enumerate all 125 assignments and four tolerances `{0,1,2,4}` eighth-units across three contracts and three actions; add a missing-context control. Candidate computes minimax residual over complete assignments; an independently written `Fraction` oracle reconstructs residuals and decisions from the raw input. Nested decision input/output and six preconditioned non-identity mutations. Host-only, no GUI/model/network/external effect; no exact container lease is assigned and the finite CPU-only enumeration is the smallest construction boundary.

**D.** PASS scoped iff 144 matrix rows reconcile exactly; exact cycle minimax=0; near cycle minimax=2 ticks (1/4), accepted only when tolerance≥2; far cycle minimax=4 ticks (1/2), accepted only when tolerance≥4; all `tol < minimax` reject all actions/contracts; missing context is UNKNOWN/non-admitting; T10 contract boundaries hold; 6/6 real mutations are rejected.

**C.** Tiny finite graph, fixed quarter-grid and additive residual semantics; one common clock/authority is not modeled. This tests status derivation only, not whether real interface evidence should use these residuals.

**U.** No real sensor/UI calibration, uncertainty distributions, general sheaf solver, freshness/provenance, GUI/model/task effect, runtime safety, or product claim. T5–T10 artifacts remain unchanged.

## Freeze protocol

- Freeze base current main `014069dc712d6c3f2f9805e64d16dbe943f9d09b`.
- Allocation `gluing-numeric-tolerance-5537-t11-20261001-01`; path `research/analysis/gluing_numeric_tolerance_5537_t11_v1/`.
- CPython 3.14.5/macOS arm64 host-local; shared container lane not assigned.
- Construction tests before freeze; one runner then one separate auditor only after exit 0; no retry or post-freeze edits.
