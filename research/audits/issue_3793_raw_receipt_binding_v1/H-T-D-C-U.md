# Issue #3793 — raw receipt byte-binding audit

Allocation: `issue3793-raw-receipt-byte-binding-orbstack-01`.

## H / T / D / C / U

- **H:** The prior audit checks JSON validity and strict-prefix semantics but does not bind the retained accepted payload and delivered prefix bytes/lengths to the frozen raw producer/downstream receipts. Same-length post-prefix replacement and shortening the prefix by one byte may therefore evade the current predicates.
- **T:** Against exact PR #3745 head `8bac49525c93835a69b6d441740a1c424faaecb2`, run a fresh independent raw-only auditor: untouched baseline, then same-length `/out/attempt` → `/bad/attempt` accepted-payload mutation, then delivered prefix 23 → 22 bytes. Assert rejection codes specifically identify producer accepted digest/count and downstream prefix digest/count binding.
- **D:** One OrbStack Docker `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `linux/arm64`, `--network none`, read-only input, read-only root, separate empty output. No CLI/backend, GUI, model, or input; one container invocation. STOP on image/platform/mount mismatch.
- **C:** Inputs are copied byte-for-byte from immutable PR head #3745 and hashed before execution. The auditor independently verifies baseline bytes against raw receipts, rechecks each mutation in memory, and requires the relevant binding error codes. Predecessor evidence is not modified; only this successor result path is writable.
- **U:** Two finite corruption probes and retained synthetic evidence integrity only. No experiment rerun, OS/network truncation, caller behavior, production reliability, or closure of #3711.

## Source identity

- PR #3745 head: `8bac49525c93835a69b6d441740a1c424faaecb2`
- Main/base at branch creation: `8e82c5bf25d63c70c188d972cdf320533bf4b310`
- Frozen predecessor `raw.json` SHA-256: `3f51dc5a4c9c8acb48fc2929a8219260575271e5794cd5bd4afedf6f712afc73`
- Producer receipt: 246 bytes, SHA-256 `e8ef9f6dd897325a22b1927d27e7fba2948051bb309cc472bbf2a1bfaba863d1`
- Downstream receipt: 23 bytes, SHA-256 `0450145d98f8ff197766d91827a438db1aa5800d556b4bee24eb57b33e168d4a`
- Image digest: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`

`input/` is a verbatim snapshot of the subset of predecessor files consumed by this audit. `INPUT_SHA256SUMS` freezes every file. The predecessor branch/tree remains untouched.
