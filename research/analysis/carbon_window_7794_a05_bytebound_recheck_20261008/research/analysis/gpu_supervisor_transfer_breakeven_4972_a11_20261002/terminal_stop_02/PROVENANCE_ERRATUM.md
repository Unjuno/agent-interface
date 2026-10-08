# A11 provenance erratum — append-only, 2026-10-02

This correction supplements the earlier A11 comments and terminal-stop record; it does not rewrite them.

## Reconciliation

- The prospective freeze recorded in the A11 preregistration and Issue #5882 comment 5944545376 uses base main `eacb1346866f660d9d34eb36cd9691fd8184e5ff`. The committed `FREEZE.json` at PR #6452 head `20fd2d98c11170dcdd4252e0a43aec711e8670b6` confirms that same value.
- The start-gate record `terminal_stop_02/observed_start_gate.txt` says the gate read frozen base `b0c1f12285fbbd2d4335999e727dc3211b55139d` and current main `ddc3a7771f409889fbde87d7da01944cd1a08b0f`. The checked-out A11 `FREEZE.json` also contains the b0c1 value, while the published branch freeze contains eacb.
- Therefore the gate was run against a local freeze variant that did not match the committed/preregistered freeze. The earlier comments' precise statement that the gate compared against the committed b0c1 freeze was inaccurate.
- The outcome remains pre-candidate STOP: observed main ddc3 matched neither recorded base, so no candidate, CUDA workload, or formal auditor was invoked. Counts remain candidate=0, CUDA=0, formal auditor=0, retries=0. This is not a scientific performance result and supports no crossover claim.
- Preserve both original values and raw files as historical evidence. Do not rerun or re-freeze this consumed A11 allocation; any future scientific attempt requires a separately authorized fresh allocation and a new freeze.

## Scope of this correction

A11 is closed as `STOP_BEFORE_CANDIDATE_FREEZE_PROVENANCE_MISMATCH_AND_MAIN_ADVANCED`. The CPU-only construction PASS remains scoped construction evidence. WSLc swap/cgroup enforcement remains unestablished. No image, container, process, or user data is modified by this correction.