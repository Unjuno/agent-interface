# Formal run 01 — route-efficiency multiverse accounting

Disposition: PASS_METHOD_SCOPED. This validates finite synthetic accounting and guard behavior only; it is not evidence that one route or product is faster.

Frozen allocation: route-efficiency-multiverse-5827-t0-20261001-01 (Issue #5827). Frozen input commit: f6357ed20b8e144cc09bb87d81e2a43ac95bf0cd; main base: 2776c9405c51ef279bf6fd6186b2b1531bbff31d.

## Findings

- Five expected cohorts were emitted and independently matched.
- Stable positive fixture retained all 3/3 pairs and gave a paired task-completion mean delta of -4,000 ms (guarded minus direct); cold=2, warm=1. This is fixture arithmetic only.
- Definition-sensitive cohort returned HOLD_ROBUSTNESS_FOR_THAT_CLAIM across finite bounds [-5,000, +25,000] ms.
- Different estimands stayed separate: the tradeoff fixture reports task completion -10,000 ms and human residual work +15,000 ms.
- Safe-stop control returned HOLD_OPEN_CENSOR_BOUND for completion while separately retaining typed-safe-termination -4,000 ms.
- Collateral-error control returned FAIL_COLLATERAL_ERROR and was ineligible.
- Missing token input returned HOLD_MISSING_DATA, not zero. Capture-to-effect and delivery-to-effect remained distinct clocks.

## Audit and limitations

Independent raw-only audit: PASS_METHOD_SCOPED, 5/5 cohorts matched, zero errors. The audit does not establish source-data provenance, human scoring validity, external generalization, route performance, latency benefit, or safety outside the fixtures. No model was run.

Docker Desktop was available as a local application/context, but its desktop-linux engine pipe accepted a bounded connection probe without returning a response. No container was started or modified. This run therefore used host CPython 3.12.10 on Windows for a CPU-only finite ledger check. This is an execution deviation, not a failed method result.

See RUN.json for exact commands, invocation counts, and input hashes; candidate-output.json and audit-output.json are the preserved formal outputs.

