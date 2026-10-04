# Issue #7741 T0c — failed negative-control gate

New hash-frozen successor after immutable T0 v1 audit failure and T0b runtime STOP. Candidate and independent raw-only event auditor each ran once and exited 0. The auditor found zero event/accounting errors and 16/16 primary shared-single-server p95 reversals, but the per-principal-queue negative control also reversed in 11/16 cells. The frozen decision therefore returns `METHOD_FAIL_OR_INCONCLUSIVE`; do not promote this to the required method PASS.

The 217,475,182-byte candidate stream is preserved losslessly as `formal_01/RAW.json.gz` and hash-bound by its receipt. This remains synthetic mechanism evidence, not an empirical, GUI, runtime, user, capacity, or safety result. See [`REPORT.md`](REPORT.md), [`FREEZE.json`](FREEZE.json), and `formal_01/`.
