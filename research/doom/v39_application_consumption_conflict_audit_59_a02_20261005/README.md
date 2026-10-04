# V39 application-consumption A01 chronology audit successor A02

## H / T / D / C / U

- **H:** The A01 saved-result auditor must derive each chronology decision from its retained DOWN and UP intervals. A coherently altered `expected_ordered` flag, status, and output interval must fail even when the aggregate remains 15 ordered and 85 incomplete rows.
- **T:** Audit the immutable A01 raw JSON from predecessor head `efb712b1aa6f01d67ed119b266ef479645cfb96a`, then create a balanced two-row chronology corruption independently for baseline and candidate. Recompute ordering from `down[1] < up[0]` and compare classification, status, and exposed intervals.
- **D:** PASS only if the untouched source audits 15/85 for both implementations and the mutation is rejected with two chronology mismatches per implementation while those aggregate counts stay 15/85. The separate raw verifier must reproduce the mismatch count without importing the candidate.
- **C:** The A01 result is deterministic projector evidence; chronology reconstruction does not establish application consumption, physical dwell, useful effect, safety, recovery benefit, or live GUI behavior.
- **U:** Audit-only CPU execution over a retained JSON artifact. No game, X server, GUI, model, or input allocation is part of this successor.

## Result

The v1 saved auditor trusted each row's stored `expected_ordered` bit. A scratch-copy mutation flipped one truly ordered row and one unordered row per implementation while preserving the 15/85 total; v1 still returned PASS. This A02 candidate recomputes ordering directly from the interval endpoints, rejects all four changed classifications, and retains the untouched 15/85 result. The original A01 raw and audit remain unchanged in their predecessor package.

## Reproduction

```powershell
python -m unittest -v research.doom.v39_application_consumption_conflict_audit_59_a02_20261005.test_audit_a02
python research/doom/v39_application_consumption_conflict_audit_59_a02_20261005/audit_a02.py --input research/doom/v39_application_consumption_conflict_audit_59_a02_20261005/input/A01.json --output-dir research/doom/v39_application_consumption_conflict_audit_59_a02_20261005/formal
python research/doom/v39_application_consumption_conflict_audit_59_a02_20261005/verify_a02.py
```

The formal output is one audit-only invocation; `verify_a02.py` independently recomputes each row from the saved source and mutation files.
