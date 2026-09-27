# Issue #2295 allocation-01 — retained formal STOP/HOLD

Allocation: `issue2295-action-receipt-recommit-20260922-01`
Public preformal freeze: `f8b113614b5dafa38d2de5ddb9fec257769ab4e1`

## Disposition

- execution: `STOP_EXTERNAL_EXECUTION_TIMEOUT`
- scientific/formal: `HOLD_FORMAL_INCOMPLETE`
- formal invocations: 1
- same-ID reruns/resumes/replacements: 0
- post-freeze tuning: 0

The outer execution tool terminated at its 180 second envelope before the frozen 54-case denominator completed. The formal runner did not emit a terminal stdout record. `RAW.json` and `END.json` are absent. The allocation is consumed and must not be resumed or rerun.

## Retained first outcome

- 49 complete rows in `formal-01/RAW.partial.json`.
- A 50th case directory was created but did not produce a completed row.
- No owned experiment/Xvfb processes remained after the outer stop.
- Formal stdout/stderr are retained exactly as observed (both empty).
- The seven frozen scientific source hashes matched immediately before invocation.

A separate read-only raw audit over the 49 complete rows exits 1 and reports `FAIL_OR_HOLD_RECOMMIT_RECEIPT_RUNTIME_BOUNDARY` with the sole error `ROW_COUNT:49`; all 10 corruption controls reject.

Incomplete-prefix observations, not acceptance claims:

| policy | complete-prefix admissions | complete-prefix effects | directed unsafe cases |
|---|---:|---:|---:|
| REUSED_ID | 17 | 17 | 12 |
| FRESH_EPOCH | 13 | 13 | 8 |
| COMPOUND | 5 | 5 | 0 |

These are unbalanced stopped-prefix counts, not rates and not PASS evidence. Construction counterexamples are preserved separately and are not pooled into the formal denominator.

## Scope

Private Xvfb/Tk fixture and XTEST input only. No model/provider, user desktop, Docker/OrbStack image-attested replication, production runtime mutation, natural race-frequency, latency/token or integrated desktop acceptance claim.
