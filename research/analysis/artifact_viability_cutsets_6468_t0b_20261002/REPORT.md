# Formal report — #6468 T0b artifact-viability method test

## Disposition

**`SUBSUMED_BY_12` (scoped synthetic result).** The independent auditor accepted the complete 6-case / 12-route candidate output, reconstructed both contracts' minimal cut sets, observed zero strict-TaskContract versus dependency-ledger decision disagreements, and rejected all five frozen raw-output mutations. The dependency ledger supplied cut-set explanations but no additional viability decisions in this fixture.

Only one route pair produced the planned equal-partial inversion: document Route A and B both scored 8, with A viable and B failing claim-citation binding. In the spreadsheet formula case, A scored 8 and B scored 7 (formula and range failures), so this case was not a second equal-score inversion. Thus the exact frozen `METHOD_PASS_SCOPED` gate requiring both planted inversions was not met; no method PASS is claimed. The sub disposition follows the predeclared zero incremental-decision-value rule. The original Issue T0's minimum single equal-score inversion and no-inversion control were present.

## Frozen method

- **H:** Weighted partial-check completion can tie or improve for a route that fails a mandatory artifact-viability condition; dependency cuts should preserve critical/cosmetic/UNKNOWN boundaries.
- **T:** Two seven-check synthetic contracts, six paired route cases, weighted partial score, strict TaskContract, exhaustive minimal-cut-set status, independent reconstruction and five mutation controls.
- **D:** Method PASS required both inversions, controls, full reconstruction and all mutations rejected, plus incremental dependency-vs-strict decision value. Exact decision agreement yields `SUBSUMED_BY_12`; discrepancy yields `FAIL_METHOD`.
- **C:** A strict required-effects TaskContract may express the same viability boundary; the authored synthetic oracle is not independent of the fixture's assumptions.
- **U:** No rendered pixels, real document/spreadsheet engine, user purpose, delivery, GUI/model route, human adjudication, time/cost or real-world usability were measured.

## Exact observations

| Case | Route A (partial / strict / dependency) | Route B (partial / strict / dependency) |
|---|---|---|
| Document citation | 8 / PASS / PASS | 8 / FAIL / FAIL |
| Spreadsheet formula | 8 / PASS / PASS | 7 / FAIL / FAIL |
| Cosmetic-only failure | 11 / PASS / PASS | 8 / PASS / PASS |
| Missing export | 11 / PASS / PASS | 10 / FAIL / FAIL |
| Render evidence unknown | 11 / PASS / PASS | 10 / UNKNOWN / UNKNOWN |
| No-inversion control | 8 / PASS / PASS | 11 / PASS / PASS |

The minimal cut sets are retained in `raw_candidate.json` and `raw_audit.json`. For the document they are singleton failures of claim-citation binding, export, source fidelity or structure, plus the pair `{accessible_text_export, render_readable}`. For the spreadsheet they are singleton failures of export, formula, formula range or source values, plus `{accessible_summary, chart_visible}`.

## Execution and audit

- Pre-freeze construction unit suite: `python -m unittest -v test_contract.py test_auditor.py` — 12/12 passed.
- Formal candidate, exactly once: `python candidate.py fixture.json raw_candidate.json` — exit 0; SHA-256 `2cf74c7a53dbb536564e3ac40b3964ad4b863d76d1142601b615019b13a6a5d6`.
- Independent auditor, exactly once: `python auditor.py fixture.json raw_candidate.json FREEZE.json raw_audit.json` — `ACCEPTED`, exit 0; SHA-256 `e9e3575adf188c4b73206ac5b626762955746b8bc98981d779102d9d3dc19aab`.
- Five mutation controls rejected: critical-failure gate removal, UNKNOWN→PASS, citation target swap, double-counted score, and cosmetic failure promoted to hard gate.
- `FREEZE.json` preserves the pre-run zero counters. `RUN.json` is the append-only post-run count and disposition record. `SHA256SUMS` covers final package files.

No retries, model, GUI, network, external document, or recipient were used. This does not establish any live artifact capability or interface efficiency. T1 is not authorized by this result and requires a separate collision-free proposal under #6468.
