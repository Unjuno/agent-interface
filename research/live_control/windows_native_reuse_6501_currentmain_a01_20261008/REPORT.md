# Windows reused-worker stale-cancellation evidence: current-main rescue check

Date: 2026-10-08 JST

## H/T/D/C/U

- **H:** A cancellation request associated with an old read/generation may terminate the same worker's later read if cancellation is issued after that worker has advanced; a generation check outside the worker admission lock is insufficient for the directed pending-B schedule.
- **T:** Preserve and revalidate the already completed Windows T02 evidence capsule on current main. Do not replay its consumed Windows native cells, model, auditor, or mutation driver.
- **D:** Original PR #7139 head `7033bb7fef7593f9d11ffe6a6f0b9934c7cd70b7`; current-main merge commit `b39fb48148e7e5cc69b9c5b2c82336666cb551ea`, second parent main `d4eaac02eced2e6ebf2e8d29642343048661d71b`. The PR diff against current main remains exactly 70 additive evidence files and no runtime/code adoption. SHA256SUMS covers 61 targets; SHA256SUMS_V2 covers 69 targets and includes the v1 manifest; all target bytes were recomputed from Git blobs and matched.
- **C:** Both SHA manifests pass 61/61 and 69/69; workspace index 161 top-level dirs PASS; strict analysis index 779 retained result dirs PASS. Existing report preserves four once-only Windows cells, 120 events, causal-audit v1/v2 false accepts and v3 correction, source/dependency limits, and all raw/negative-control outcomes. No archived producer/helper was executed.
- **U:** Result is a directed Windows CPython thread-reuse counterexample, not generic worker-pool safety, arbitrary I/O preemption, handle ABA protection, a pre-I/O race result, task effect, performance, or current runtime adoption. PR #7139 remains Draft; its current proposal requires fresh eligible same-proposal content approvals and a separate current-tree application/ownership/cancellation/policy gate. No such approval/certificate is present. Keep #7139 and its source branch; do not merge main or delete the predecessor.

## Commands

Manifest checks and index commands are recorded in `COMMANDS.txt`. Checksummed inputs were read directly from Git blobs because this checkout sparsely omits the large archive directory; no archive bytes were rewritten.
