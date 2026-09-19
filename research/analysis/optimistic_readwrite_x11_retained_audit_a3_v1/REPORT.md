# Retained #1750 optimistic-X11 audit A3

Decision: **PASS_RETAINED_OPTIMISTIC_X11_AUDIT_A3_SCOPED**.

This is an audit-only successor to #1750 and workflow successor to #1795. It did not execute X11/Tk/Xvfb cases and does not relabel either predecessor.

## Evidence binding

A3 consumed only the exact retained #1750 evidence:

- raw 12-row SHA-256 `230a7253f6b013a728feab0f8d5d3b75b12b9d1c47ddf0856b223b67e7b0fba8`;
- raw parent RESULT SHA-256 `180f6a75a8ed2876cf93d5abfd0d07e4fe2d3b90f0a08db7d2fb481c7a554fa2`;
- original failed parent AUDIT SHA-256 `dae25b7c69fed2d04236a02e1abf66230f1991f4803132d492b709eabae554b8`;
- parent disposition exactly `FAIL_INTEGRITY_AUDIT_GATE_COUNT`.

The A3 auditor reconstructs the parent compressed evidence in memory and does not import #1750 candidate/formal code.

## Recomputed result

All seven original scientific gates independently recompute true:

1. allocation;
2. complete case/cleanup;
3. distinct XIDs;
4. independent-resource behavior;
5. shared-global candidate behavior;
6. surface-only unsafe discriminator;
7. external-stale behavior.

- rows: **12**, exactly3/family;
- candidate stale G0 effects: **0**;
- surface-only comparator stale G0 effects: **3/3**;
- parent RESULT summary matches recomputed values;
- parent original failed audit identity matches and remains immutable.

A3 scientific audit invocations1, A3 reruns0, parent live reruns0. Fixed copied-evidence corruption controls rejected **6/6**. Post-audit source identity **3/3** exact.

## Interpretation

The combined provenance is deliberately two-stage:

- #1750 remains **FAIL_INTEGRITY_AUDIT_GATE_COUNT** because its frozen auditor was wrong;
- #1795 remains **STOP_WORKFLOW_INTEGRITY** because it executed before source freeze;
- #1799 establishes that the exact retained #1750 raw rows satisfy the original seven scientific conditions under an independently source-frozen corrected audit.

Therefore future work may cite the scoped X11 transfer only as **retained parent raw validated by successor audit #1799**, never as a relabeled parent PASS.

This still does not establish XTEST routing, application semantics, dependency completeness, speedup, tokens, human tempo, or production scheduling.
