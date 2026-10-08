# #5126 v4 — pinned corpus and effect identity audit

## H — Hypothesis

A raw-only auditor that pins the v1 input corpus and independently derives the sole qualified effect ID rejects stale-digest row substitution and jointly corrupted candidate/oracle effect IDs.

## T — Method

Three construction tests ran before freeze. Then exactly one synthetic 13-row run and one raw-only audit were allocated. No game, model, GUI, live input, network collection, GPU, or container was used. The raw corpus is synthetic and input-authority is false.

## D — Result

**PASS** for this narrow audit-integrity gate: candidate/oracle agree 13/13; the frozen input corpus and exact ordered raw rows match; raw-derived task/physical classifications and effect identity pass; both corruption controls are rejected. Result SHA-256: `6b29be80244c46db2975fd219aa196edef8b1aa9c23e9d79b18fc319af86248b`. Audit SHA-256: `8cb61134622f452155ca5a2b4b6a4884c8cbee2e1f12baaa1b493fb69d876425`.

## C — Interpretation

This v4 successor addresses the two audit-integrity defects identified on PR #5131. It supersedes v3 only for audit-integrity claims; v3 files and formal output are preserved. v3's earlier PASS is not evidence for the stronger v4 gate.

## U — Unresolved / stop boundary

This is synthetic contract evidence only. It does not establish current producer source identity/epoch availability, live task efficacy, efficiency, runtime readiness, or integration. The #5141 source-schema disposition remains `HOLD_SOURCE_IDENTITY_INSUFFICIENT`; no container slot was assigned, so container execution was not attempted.
