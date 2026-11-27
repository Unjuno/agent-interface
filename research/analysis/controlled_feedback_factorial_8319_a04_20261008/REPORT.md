# A04 result — scoped finite factorial contrasts

## Gate

`PASS_ANALYSIS_SCOPED` and `PASS_ANALYSIS_AUDIT_SCOPED`. The analyzer read the immutable A01 raw once (SHA-256 `ecffd8121a289d3533c94373c8f7aba50d9c349ffd5db534e46db16522897e9d`) and summarized 400 rows across four cells and 100 paired seeds. The independent raw-only auditor reconstructed the result and rejected all 6/6 frozen output mutations. Construction tests passed 5/5 before freeze. No retries occurred.

## Finite-fixture results

Numbers below are exact rational means of the seed-paired differences, `FULL - CONTROLLED`, for each update rule. The interaction is the CASE_PATCH feedback difference minus the STRATUM_PATCH feedback difference.

| Metric | CASE_PATCH | STRATUM_PATCH | Interaction |
|---|---:|---:|---:|
| Development accuracy | 9/160 | 1/160 | 1/20 |
| Fresh accuracy | 0 | 1/160 | -1/160 |
| Optimism | 9/160 | 0 | 9/160 |

The four cell summaries and full distributions (exact mean, median, minimum, maximum, and sign counts) are in `results/analysis.json`. These are descriptive contrasts in the authored finite simulator fixture only. They provide no p-values, population inference, or evidence about actual researcher feedback behavior.

## Preserved predecessor state

A01 remains `HOLD_AUDITOR_GATE_FAILURE`; A02 remains `PASS_AUDIT_ONLY`; A03 remains `STOP_ANALYSIS_INPUT_OR_CONTRACT` before analysis due to its missing output parent. A04 is a separate saved-data allocation and does not repair, retry, or alter those records. No candidate or auditor simulation was run.
