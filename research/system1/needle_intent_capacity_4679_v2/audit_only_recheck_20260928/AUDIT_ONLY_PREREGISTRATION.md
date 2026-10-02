# Issue #4778 audit-only allocation — 2026-09-28

## H — hypothesis

The unchanged three-seed raw records can be independently reconstructed under the exact Issue #4778 decision gates once the frozen raw-only auditor's stale allocation identity literal is corrected, with no model retraining and no criterion changes.

## T — treatment and freeze

- Allocation: `needle-intent-capacity-4778-audit-recheck-20260928`.
- Main/base: `f3dc0f18b0aaef241a6cd34124b68439c3434b05`.
- Branch: `research/needle-intent-capacity-4778-audit-recheck-20260928`.
- Additive path: `research/system1/needle_intent_capacity_4679_v2/audit_only_recheck_20260928/`.
- Input is the three already-published immutable raw files from #4778:
  - `seed_4153201.json` — 913,936 bytes, SHA-256 `efc40b1776f9df4be05ee2518af7552b5ccd6c4d24acc5e3737dc4a545b59ee1`
  - `seed_4153203.json` — 914,069 bytes, SHA-256 `8128339b66fa330f19d0ba6e661fa8de065ef6b9b2d862b92862af7f0a87e32f`
  - `seed_4153207.json` — 914,042 bytes, SHA-256 `4fb34391efee50bd7d1991e4595bf1348ff5027eb25d6488c556c2e3b9660aed`
- Start with the exact frozen audit source Git blob `d9d058e50e8c25bb4b88967668433026229a9d5c`, SHA-256 `859991d9e7496681bb786b9bca35ef2f7644180b5d108be636eea9f664935156`. The audit-only executable differs in exactly one literal: expected allocation `needle-intent-capacity-4679-v1` → `needle-intent-capacity-4679-v2`. The script verifies byte hash and single-literal diff before starting Docker.
- One read-only-source, network-disabled auditor container only: image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, 1 CPU, 2 GiB, 64 PIDs. The raw mount is read-only; only a new audit-output mount is writable. No training fit, model update, or seed use. One attempt; no retries.

## D — unchanged frozen gates and interpretation

Retain every gate from #4778: width-64 accuracy ≥0.97, exact-all-intents ≥0.90, disagreeing-intent accuracy ≥0.96, OUT_OF_SCOPE YIELD recall ≥0.995, action on teacher-YIELD ≤0.01, forbidden-effect proposals ≤0.01; teacher-disagreement base fraction ≥0.50 for both intent-aware arms; state-only exact-all-intents ≤0.60; invalid-intent fail-closed controls; recomputed predictions and all 10 corruption controls; zero audit errors. Capacity adjudication remains exactly as preregistered.

Any audit-only result is explicitly additional forensic evidence. It cannot erase or upgrade the consumed allocation's registered `STOP_AUDIT_INTEGRITY` from its frozen original audit; the original audit and post-hoc audit remain untouched.

## C — confounders

This reuses the same reconstruction algorithm with only the expected allocation identity corrected; it is not an independently designed second trainer or a new statistical replication. The previous post-hoc audit omitted the teacher-disagreement condition; this recheck deliberately preserves it and every other original threshold.

## U — limits

This cannot establish a clean preregistered formal PASS, training reproducibility, natural-language intent fidelity, online learning, GUI performance, action safety, runtime suitability, or product readiness. It only tests whether unchanged raw data satisfy the original numeric and integrity checks after a mechanical identity correction.
