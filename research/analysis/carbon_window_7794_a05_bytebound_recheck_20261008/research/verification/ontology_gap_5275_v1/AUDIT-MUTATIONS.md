# Independent auditor mutation controls — addendum

The frozen first raw result and AUDIT-01 were not changed. A separate test harness exercised the raw-only auditor on deep copies of FORMAL-01.

- Baseline frozen raw accepted with zero audit errors.
- Six mutations rejected: changed row prediction; missing case; altered registry source identity; nonzero dispatch; changed denominator/mismatch count; relabeled scientific disposition.
- Tests: 7/7 passed on host CPython 3.11.9 with `python -B`, streaming the exact GitHub-readback auditor/test sources in memory; no local result files.
- Auditor Git blob SHA-1: 62d1e2a9991e7bddf511e40c5b74597877fc1b23.
- Mutation-test source Git blob SHA-1: d9b453beebf8c0b050f82204ac234b5aa57ef359.
- Frozen first raw Git blob SHA-1: 040edd759c81c4d95df68d3641a8808302e2d6d4.
- Mutations were applied only to in-memory deep copies; FORMAL-01 and AUDIT-01 remain immutable.

These controls test audit integrity for selected fields, not semantic correctness of the independent oracle or broad adversarial resistance.
