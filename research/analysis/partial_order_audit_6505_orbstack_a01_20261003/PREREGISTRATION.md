# Issue #6505 — A01 audit-only preregistration

## H / T / D / C / U

- **H:** A fresh, independently implemented raw-only auditor can reconstruct all 11,111 retained #4889 rows and their aggregate claims from exact published bytes, and reject eight effective copied-evidence mutations, without rerunning the consumed candidate or changing its original `HOLD`.
- **T:** One audit-only invocation in OrbStack. Rebuild the retained ZIP from its two frozen base64 parts; validate Git blob identities, archive/raw hashes and lengths, then independently enumerate the reducer's reachable states, pairwise commutativity, all words through length four, and all legal topological orders. Compare every raw row and summary field. Separately mutate copied records, confirming every mutation changes its target value and is rejected. Candidate, original runner, and original auditor invocation counts are zero; the successor auditor runs once; retries are zero.
- **D:** `PASS_INDEPENDENT_AUDIT_SCOPED` requires exact source/archive identity, byte/CRC/row-count agreement, exact independent reconstruction of every raw row and summary, confirmation of the retained historical 7/8 failure, eight effective mutations rejected, and no errors. Any source or semantic disagreement is `FAIL_AUDIT`; missing/inconsistent frozen inputs are `HOLD_SOURCE`; infrastructure failure before audit completion is `STOP_INFRA`. No retry or post-result repair.
- **C:** The original raw was already independently rederived in #4889 and the known defect is its mutation harness; a fresh implementation may find no semantic issue. Shared assumptions about the finite reducer remain possible.
- **U:** Finite authored reducer only. This does not prove the reducer models real event stores, GUI/runtime commutativity, concurrent effects, or safe production replay; does not upgrade the historical candidate PASS beyond its original scoped claim; and makes no storage/performance/product claim.

## Frozen lineage and inputs

- Issue: #6505; motivating issue #4889; construction precedent #4914; evidence-preservation PR #5393.
- Frozen base commit: `b100d9acee4ec99490b2e97066ec6af5312f1ed9`.
- Original raw SHA-256: `a25bc4a9e6cf845fb5b446b1d2d5071bd26909679efcc535372fdf77b58b4eb8` (3,241,590 bytes; 11,111 JSONL rows).
- Original archive SHA-256: `a127e04d2fcce672f3ce5cc6f20d2af0e1f85b34ac16116e9e5a518e7c358f6b` (104,640 bytes; single member `RAW.jsonl`).
- Original candidate, reducer, and audit are inputs for identity verification only; none is executed or imported.
- Fresh auditor source and all gates are frozen in `FREEZE.json`; exact container invocation is in `RUNBOOK.md`.

## Runtime / isolation

OrbStack Docker Engine, linux/arm64; cached `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. Pull is forbidden. The container will have network disabled, read-only root and repository source, a separate writable output directory, 1 CPU, 512 MiB configured memory, 64 PIDs, all capabilities dropped, no-new-privileges, and a non-root UID. Configuration/inspect evidence is retained; effective limits are claimed only to the extent directly observed in inspect/runtime metadata.

## Invocation budget

- Original candidate/reducer: 0 (consumed predecessor allocation; do not run).
- Original auditor: 0 (consumed predecessor allocation; do not run).
- Successor construction tests: host-only and separate from formal audit.
- Successor audit-only container invocation: exactly 1 maximum.
- Retries, replacements, threshold changes after audit, or outcome-driven controls: 0.
