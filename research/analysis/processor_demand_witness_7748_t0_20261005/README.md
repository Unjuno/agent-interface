# Issue #7748 T0 — finite processor-demand witness method

Scoped CPU-only method experiment on six hash-frozen synthetic traces. The candidate interval-demand oracle and independently implemented exhaustive slot scheduler agree on every eligible control/all-jobs scope; the bad best-effort-first policy misses a control deadline on an oracle-feasible trace. Non-preemptive input returns UNKNOWN and missing execution cost returns HOLD. See [`REPORT.md`](REPORT.md), [`FREEZE.json`](FREEZE.json), and `formal_01/` for exact commands and receipts.

This does not read or reinterpret #7722's consumed allocation. It establishes no host scheduler, WSL/container quota, physical release, real-time runtime, or product claim.
