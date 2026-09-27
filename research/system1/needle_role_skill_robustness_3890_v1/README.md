# Issue #4479 — role-skill graph seed robustness

A ten-seed successor to the scoped cross-process reload PASS in #3890. It tests seed robustness after a narrow role-C accuracy pass, not whether predecessor results should be revised.

- Allocation: `needle-role-skill-robustness-3890-v1`
- Seeds: 3792, 3892, 3992, 4092, 4192, 4292, 4392, 4492, 4592, 4692
- Base: #3890's role adapters and data-only skill graph
- Required gate: all 30 seed×role quality cells ≥0.90; exact builder/two-loader predictions; package hash binding/immutability; current-generation A→B→C and fail-closed controls
- Execution: cached CPU Docker only, no network, no retries
- Formal status: NOT RUN until source/freeze readback is recorded
- No model/runtime promotion is implied

See `PREREGISTRATION.md`, `ISSUE_CONTRACT.md`, `SOURCE_PROVENANCE.md`, and `CONSTRUCTION.md`. The previous #3890 result and audit chronology remain unchanged.

