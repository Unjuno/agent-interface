# Carry sparse single-mint validation to current main

Current main `bc10001a7a5e5648360d5cfa209248b65f15aacd` still accepted sparse coordinate arrays in the guarded single-mint caller: JavaScript `Array.prototype.every` skips array holes. This meant a two-element pair with a deleted slot could pass the caller's local type check and reach the host.

The current-main patch materializes the pair with `Array.from(value).every(Number.isSafeInteger)`, matching the existing batch-mint behavior. The focused regression first failed as expected in six sparse-hole cases (20/26 passing); after the one-line fix, the complete `runtime/host_v1` Node suite passed 287/287 with a fresh evidence root, the `runtime/integration_checks` helper included, and `--experimental-vm-modules`. The initial unconfigured full-suite attempt is preserved separately with its 13 environment failures. Raw TDD and suite logs are retained in this packet.

PR #8354's code was three commits ahead and 1,382 behind current main; its historical head is not merged directly. Its original custody, evidence payload, README, and checksum file were carried byte-for-byte from head `31f52fedfc26182e58960dcc8ec5a5ecc3577c38`; the three recorded SHA-256 values were checked against the Git blobs. The older approval-count and reviewer wording in its dated text is historical. The current PR must use actual technical checks and repository protections only: current main has no branch protection or repository rulesets, and this transfer adds no fixed reviewer quorum.

This is a caller-boundary correctness fix and evidence transfer, not a scientific allocation replay or proof of actual GUI effect, physical input, WSLc, MAP01, reliability, or integrated efficiency. It references Issue #57 without closing it.
The full-suite TAP logs, including the initial setup failure, are gzip-compressed byte-for-byte; compressed and uncompressed SHA-256 values are recorded in `verification.json`.
