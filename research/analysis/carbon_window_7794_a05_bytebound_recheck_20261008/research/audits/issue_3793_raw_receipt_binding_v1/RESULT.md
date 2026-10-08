# Result — Issue #3793

Disposition: `PASS_AUDIT_BINDING_SCOPED`.

One OrbStack Docker run on Docker 29.4.0, `linux/arm64`, pinned image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, network disabled, read-only source/input, separate output mount. Exit code 0.

- Baseline reproduced 246 accepted bytes / SHA-256 `e8ef9f6dd897325a22b1927d27e7fba2948051bb309cc472bbf2a1bfaba863d1`, and 23 delivered bytes / SHA-256 `0450145d98f8ff197766d91827a438db1aa5800d556b4bee24eb57b33e168d4a`; zero audit errors.
- Same-length accepted-body substitution remained 246 bytes and was rejected by `PRODUCER_ACCEPTED_SHA256_MISMATCH`.
- 23→22-byte prefix truncation was rejected by `DOWNSTREAM_PREFIX_SHA256_MISMATCH` and `DOWNSTREAM_PREFIX_BYTE_COUNT_MISMATCH`.
- Machine-readable output: [`output/RESULT.json`](output/RESULT.json).

This validates only receipt binding and the two specified mutations on retained synthetic evidence. No CLI/backend dispatch or GUI/model/input occurred; it says nothing about OS/network truncation, general caller behavior, or production reliability. All PR #3745 predecessor files remain immutable in their original branch; this successor stores a hashed input snapshot.
