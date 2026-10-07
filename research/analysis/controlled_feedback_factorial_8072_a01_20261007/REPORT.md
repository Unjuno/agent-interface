# Issue #8319 A01 — crossed feedback × update-rule probe

## Disposition

**HOLD_AUDITOR_GATE_FAILURE.** The frozen candidate ran once and exited 0, producing all 400 preregistered rows. The separate frozen raw-only auditor ran once and exited 1. Its output is retained unchanged. No candidate, auditor, repair, or retry was run after that outcome. This is not a validated scientific result.

The auditor output says `status=FAIL`, `checks=400`, `errors=[]`, `mutations_rejected=[]`, and `mutation_controls=6`. Read-only source diagnosis found a formal-entrypoint bookkeeping defect: `mutation_checks()` returns the names of undetected mutations (empty means all six were rejected), but `main()` treats a list length of six as the success condition. The pre-freeze construction test checked that the helper returned an empty undetected-mutation list, but did not exercise the CLI success/exit contract. The formal audit gate therefore failed despite the helper test; do not infer that the auditor invocation passed or silently convert its exit status.

## Frozen design and execution

- Base: `main@798ac5ad709168ff1d27b115f10f4f96b126bb71` (also matched by `git ls-remote` immediately before freeze).
- Allocation: `8072-UPDATE-RULE-FACTORIAL-8319-A01-20261007`.
- Design: seeds 0–99 × two feedback modes × two update rules = 400 rows. Five query/proposal slots per cell; the unsafe proposal is disclosed exactly and vetoed; fresh-cohort outcomes are read only after candidate lock.
- Runtime: native macOS arm64, CPython 3.14.5, standard library only. This T0 did not require a container and makes no isolation claim.
- Construction before formal freeze: 4/4 unittest tests, py_compile, and `git diff --check` passed. An earlier pre-freeze construction assertion incorrectly expected six undetected-mutation names; it failed, was corrected before freeze, and the frozen suite then passed. No formal output existed during that correction.
- Formal commands, each once: `python3 candidate.py results/candidate.json` (exit 0); `python3 audit.py results/candidate.json results/audit.json` (exit 1). Retries: 0.
- Freeze manifest SHA-256: `d2c704b4cf96b104ba58d4729fdb565681e93950fc9dcf04962cb3708397e130`.
- Candidate raw SHA-256: `ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d`.
- Auditor output SHA-256: `f05f69b4dc3f6bb06926f9a2d1fc4bb7d62749f6d42a7cd873bb8b49b00ae084`.

## Descriptive raw-only summaries — unqualified

The following aggregates were computed from the candidate JSON with read-only `jq` after the failed audit. They are descriptive, not independently audit-qualified evidence:

| Feedback | Update rule | n | Mean development accuracy | Mean fresh accuracy | Mean optimism | Exact safety vetoes |
|---|---|---:|---:|---:|---:|---:|
| CONTROLLED | CASE_PATCH | 100 | 0.63750 | 0.60000 | 0.03750 | 100 |
| FULL | CASE_PATCH | 100 | 0.69375 | 0.60000 | 0.09375 | 100 |
| CONTROLLED | STRATUM_PATCH | 100 | 0.90000 | 0.90000 | 0.00000 | 100 |
| FULL | STRATUM_PATCH | 100 | 0.90625 | 0.90625 | 0.00000 | 100 |

On this authored fixture, the descriptive FULL-minus-CONTROLLED optimism contrast is +0.05625 for CASE_PATCH and 0 for STRATUM_PATCH (difference-in-differences +0.05625). This pattern is consistent with update-rule dependence, but the frozen independent audit did not complete successfully, so it is not promoted as a validated finding and does not adjudicate #8072 A02.

## Scope and preservation

Preserves #8072 A01/A02 and PR #8083 unchanged. No actual researcher, GUI, model, privacy, generalized holdout performance, product need, or real safety claim follows. No runtime or hosted workflow was changed. The next legitimate validation would require a distinct audit-only successor allocation with a corrected formal audit contract; this allocation itself is consumed and must not be rerun.
