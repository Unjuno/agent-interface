# Issue #6565 — candidate-card parity T0

## Disposition

**`PASS_METHOD_SCOPED` for deterministic card-construction and auditor sensitivity only.** The candidate emitted the frozen 4-case × 3-presentation matrix (12 rows). The independent auditor reconstructed all 12 unique rows without importing candidate code, reported zero errors, and rejected all six preregistered mutations: recipient swap, format swap, missing agent provenance, unsupported quality endorsement, oracle-label leakage, and candidate-digest alteration.

This is not a human study and is not evidence that constraint-first presentation changes recall, approval, false acceptance, decision burden, or preference. No participant response was collected. The valid and explicit-constraint-violation cases are mechanically classified; a potentially legitimate preference revision remains `UNSCORABLE_PREFERENCE` rather than being assigned a fabricated ground truth. Agent origin and hypothetical/no-execution authority are preserved in every arm.

## Frozen method and outcome

Allocation: `PREVIEW-CONSTRAINT-PARITY-6565-ORB-T0-20261002-01`.

| Case | Policies | Expected card disposition |
|---|---|---|
| Valid recipient + PDF | 3 | Explicit-constraint compliant |
| Wrong recipient | 3 | Explicit-constraint violation |
| Wrong format | 3 | Explicit-constraint violation |
| Unspecified preference revision | 3 | Unscorable preference |

Policies alter presentation sequence only: `PREVIEW_FIRST`, `CONSTRAINT_FIRST`, `NEUTRAL_FACTS_FIRST`. Source task, source constraint, candidate effect, canonical digest, neutral facts, agent-origin disclosure, and authority are equal within each case. The independent auditor checked exact equality against its own fixed expected table.

Decision rule from the freeze: `PASS_METHOD_SCOPED` iff every expected row reconstructs exactly and all six mutation controls are rejected; otherwise `FAIL_METHOD`. Outcome: 12/12 exact rows, 12 unique keys, 0 errors, 6/6 mutations rejected.

## Execution evidence

- Source commit: `5d584c4723af48a628fbba9aa88c6ba6dbcdcbeb`; freeze commit: `c126615cc98a3f672075e30840ad7b8640c6c2ba`.
- Freeze JSON SHA-256: `4abd3ce8a4a315daf498e0d1566c5a027d47ee69a262bfa90c3fb2110ca9df37`.
- Candidate container ID: `4a4f9982ff7f253b9c7f8bbe688ba7fc5dcfbc18817f1b55947a45e18b2809a0`; exit 0.
- Auditor container ID: `cfa522b2cf90e2b07b481de3b263109256b348e8b8f697d7132f7a9ac3b5cade`; exit 0.
- Candidate: 12,292 bytes, SHA-256 `14214d109b9705f28345e30385fe59934afd45971c354edde5b5f77b21a92ac9`.
- Audit JSON SHA-256: `671984baafab1aca2acd370d523b07874e69d228a7c2814612c1b23592d4f4cd`.
- Candidate/auditor containers: one each, retries 0. Both used cached pinned Python 3.12 slim image, OrbStack, network none, read-only root/source, 1 CPU, 256 MiB requested, pids limit 64; both exited without OOM. Full argv, logs, container inspect JSON, exit markers, and machine run record are retained under `results/formal_01/`.
- Construction suite: 8/8 passed on host and 8/8 passed in a separate disposable OrbStack container before freeze. Formal containers are retained until their inspect receipts are independently checked; the pre-existing `unjuno-native-ci-6092` container was not changed.

## Limits and next boundary

The assay validates authored card parity and whether the frozen auditor detects the specified mutations. It does not validate rendered visual salience, reading/comprehension, recall, human acceptance, genuine preference change, behavioral anchoring, consent, accessibility, or task effectiveness. It does not isolate causal effects among recall-first prompts and candidate display, beyond verifying that the underlying facts and provenance remain fixed. A separately governed human T1 would need voluntary consent/privacy/accessibility review, preregistered false-acceptance and valid-false-rejection endpoints, and unchanged trusted-path/request-binding gates. This T0 does not authorize that study.
