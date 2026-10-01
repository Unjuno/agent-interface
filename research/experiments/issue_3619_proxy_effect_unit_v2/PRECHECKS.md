# Issue #3619 construction/preflight record

Formal-02 is a fresh allocation; #3610 formal-01 remains an immutable STOP.

- Pinned OrbStack image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, Linux/arm64.
- Construction unit tests include the actual runner's `wait_state(pid_hint=...)` signature and every AST callsite passing that keyword.
- Formal launcher uses `set -euo pipefail`; it verifies launcher hash, exact local image ID/platform, source/preregistration/freeze bindings, test results, and a fresh empty formal output directory before runner invocation.
- Construction GTK/Xvfb smoke is explicitly excluded from the 28 formal rows.
- Formal runner: one invocation, 28 rows, row errors 0. Independent audit: HOLD; see `evidence/formal-02/REPORT.md`.

## Construction failures retained before freeze

- The first regression-test pass caught one remaining `wait_state` call site (the duplicate-target setup) without an explicit `pid_hint`. That call was made explicit; the corrected suite then passed 2/2, AST parsing passed, and `bash -n` passed.
- The GTK construction smoke completed with `proxy-fixture:1:2`, one click acknowledgement, and one effect. It is not a formal row.
