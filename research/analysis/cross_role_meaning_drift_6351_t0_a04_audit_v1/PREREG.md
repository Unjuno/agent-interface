# Frozen audit-only successor A04 — Issue #6351

- Scope: independent posthoc audit of the already executed A03 candidate allocation; do not rerun candidate. A03 candidate/raw are immutable. Its original auditor is invalid for inference because it omitted planner dispatch and effect-owner release/effect projection checks.
- Normative Issue #6351 body SHA-256: `1e2883933a44ffd8b080a053ba3babceff8c0553703a93a0c755c68e57f5356a`.
- Inputs: A03 `raw.json`, `candidate.json`, `oracle.json`, with hashes verified against A03 `SHA256SUMS` before this audit. All rows are synthetic and source-bound to the Issue.
- H — Full role-field auditing will either confirm every projected dispatch, verifier verdict, release, effect, child obligation, and conflict flag against independent raw reconstruction, or falsify A03's PASS report.
- T — One raw-only auditor invocation; check all 8 rows × every role field and oracle; corrupt each role field in-memory for the construction gate and assert rejection. No hard-coded per-outcome counters.
- D — `AUDIT_VALID` only if every field and oracle match and all mutations are rejected. Otherwise `AUDIT_FAIL`; no retry.
- C — Candidate outputs may be correct while A03's auditor is incomplete; independent reviewer must not import candidate or A03 auditor code.
- U — Confirms only finite synthetic method records, not semantic validity of a real runtime receipt or human/model interpretation.
- One invocation, no candidate replay.
