# Result: scoped journal/state reconciliation pass

Issue: [#8300](https://github.com/Unjuno/agent-interface/issues/8300) (successor to #7949; predecessor evidence unchanged).

## Formal outcome

**PASS_JOURNAL_STATE_RECONCILIATION_SCOPED** — one frozen candidate invocation generated six deterministic cases; one separate raw-only audit invocation independently re-read the retained SQLite snapshots. Audit returned `{"case_count":6,"errors":[],"status":"PASS"}`. No formal retries were performed.

| Case | Candidate decision | Observed effect |
| --- | --- | --- |
| Baseline | `COMPENSATED_BASELINE` | Owned `x` field compensated; revision 1→2 |
| Complete disjoint `y` write | `COMPENSATED_DISJOINT` | `x` compensated, external `y=7` preserved; revision 2→3 |
| Same-field `x` write | `UNKNOWN_SAME_FIELD_CONFLICT` | No agent write; external `x=9` preserved |
| Revision advance, missing event | `UNKNOWN_JOURNAL_STATE_MISMATCH` | No write; committed external state preserved |
| Journal sequence gap | `UNKNOWN_JOURNAL_STATE_MISMATCH` | No write; state preserved |
| Journal/state value disagreement | `UNKNOWN_JOURNAL_STATE_MISMATCH` | No write; state preserved |

The old certificate is explicitly UNKNOWN after each external revision change; the disjoint case separately reports a fresh certificate at observed revision 2 before its compensation transaction. The auditor checks snapshots, journal replay, final state, compensation event, and certificate classifications; a mutation test rejects forged decisions and snapshot tampering.

## Local validation

- Construction and mutation tests: 8/8 PASS.
- `py_compile`: PASS.
- Repository analysis index: PASS, 761 indexed retained result/failure directories.
- `test_analysis_checkout.py`: 3/3 PASS.
- `git diff --check`: PASS.
- Formal runner and audit source SHA-256 are recorded in `FREEZE.json`; candidate raw output SHA-256 `7bacb35a06159c2f09dfae874eb9bba87b980f61857d76fdf36ce519e8d5a69f`; audit SHA-256 `28f12d2b6b3040a0f25d60c61a360599c37bc5d4e7891cc5b0734aaed4f3f630`.

## Limits and disposition

OrbStack image-store preflight was unavailable; this used native macOS standard-library Python/SQLite, with no container-isolation claim. This is a deterministic synthetic protocol probe, not a production implementation validation, GUI experiment, stress/concurrency test, or authorization result. The evidence supports only the six frozen cases. It does not establish that a real application's journal is transaction-coupled, complete, authentic, or protected against adversarial mutation.

Formal raw JSON, audit JSON, stdout/stderr receipts, and before/external/final SQLite snapshots are retained under `results/`; `results/SHA256SUMS.txt` verifies every retained result artifact. Source freeze and formal counts are retained in `FREEZE.json` and were recorded on Issue #8300 before execution.
