# Issue #9004 T0 run record

Allocation `9004-agreement-continuation-t0-a01-20261017` executed once after the frozen source commit and Issue comment. The run generated 40 rows (10 fixed cases × 4 arms); the independent raw-only auditor reconstructed all rows with no errors. The frozen gates are `PASS_METHOD_SCOPED`; all five mutation tests pass in normal and optimized Python. Raw and audit outputs are retained as `RAW.json` and `AUDIT.json`.

Observed descriptive counts: always-wait 4 actions in 2 cases; System-1-only 4 actions in 2 cases; agreement-only 2 actions in 2 cases; agreement-lease 4 actions in 2 cases. For the two cases with paired actions, the median synthetic inter-action gap was 1 tick for always-wait, System-1-only and agreement-lease. This does not meet the prospective 20% reduction threshold. Agreement-lease matched System-1-only in the cases where either acted; no incremental agreement advantage was observed in this finite trace family. Synthetic ticks are not measured latency.

**Disposition:** `NO_INCREMENTAL_AGREEMENT_VALUE` for this T0 trace family; method gate passes, hypothesis is unsupported here. `formal_pass=false`. No live actuation, real application, model agreement rate, physical release behavior, GUI safety, or product claim is established. No retry is authorized for this consumed allocation.
