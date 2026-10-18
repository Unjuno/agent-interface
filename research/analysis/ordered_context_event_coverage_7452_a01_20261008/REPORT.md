# Successor #7452 A01 — result

## Verdict

`PASS_METHOD_SCOPED` — the frozen finite method probe passed its independent raw-output reconstruction. This is not evidence about a real GUI, an agent, safety, or general ordered t-way efficacy.

## Execution

- Basis: current `main` at design SHA `ff4eac79dab728748862e34d650a39c8c2d811a3`; frozen implementation committed as `5a27cd6bfb`.
- Environment: host Python 3.12.13, CPU-only. No container, GUI, model, or network was used. This is a documented environment deviation, not container evidence.
- Pre-formal construction tests: 2/2 passed.
- Candidate: invoked exactly once; exit 0; output SHA-256 `1c32d9a70d65a540a8f71b136c5364a2c882b11be82e810119d10fc93e5e025f`.
- Independent auditor: invoked exactly once; exit 0; `AUDIT.json` status `PASS`; errors `[]`.
- Retries: 0.

## Findings

- Candidate and auditor independently agree on 4 context-only episodes/4 rows, 1 order-only episode/8 rows, 4 mixed episodes/32 rows, and 128 exhaustive 2-row episodes/256 rows.
- Each of the four mixed episodes covers all 16 ordered event pairs within that episode. The selected denominator is 4 context-pair assignments × 16 event pairs = 64 obligations; exhaustive comparison is 8 complete three-factor assignments × 16 pairs = 128 obligations.
- The joint context-and-order mutant is missed by each separate scoped suite and detected by mixed and exhaustive suites. Context-only and order-only controls are detected by the corresponding standalone and mixed/exhaustive suites. The negative control has no unsafe effect.
- No event pair across reset boundaries receives credit. Mixed requires 32 rows, one eighth of exhaustive's 256 rows, for the narrower selected-pair/fixed-freshness contract. This is not a claim of equivalent complete context coverage.
- Frozen drop-episode and context-collapse mutations are guarded by exact independent suite reconstruction; cross-reset credit is explicitly excluded by the episode-local oracle.

## Scope and next work

The result supports only this explicitly enumerated synthetic method contract and its seeded policy faults. It does not validate NIST conformance beyond the stated row-combination interpretation, nor real GUI histories, runtime behavior, usable coverage reduction, or safety. A later successor would need a separately frozen empirical mapping and observed fault corpus before making those claims.

See [FREEZE.json](FREEZE.json), [model.json](model.json), and [AUDIT.json](AUDIT.json) for the immutable gate and machine-readable evidence.
