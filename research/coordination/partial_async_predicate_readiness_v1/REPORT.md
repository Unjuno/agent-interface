# #4216 partial asynchronous predicate readiness — retained formal HOLD

## Disposition

`HOLD_AUDIT_CONTROL_HARNESS` for the frozen formal allocation. The 36-case runner completed once with no reruns, and the frozen raw-only auditor reconstructed all rows with `errors=[]`, but the preregistered 8/8 corruption-control gate was not met: seven controls rejected and the dropped-row control raised `KeyError` instead of returning a typed failed audit.

A separately versioned read-only `audit_v2.py` fixes only missing-row robustness. It reproduces the same raw audit result and rejects 8/8 controls, but it does **not** retroactively convert the frozen HOLD to PASS.

## Observed semantic/timing evidence

- 36/36 formal cases, 144/144 predicate-task completions.
- Paired GLOBAL_BARRIER and DEPENDENCY_READY dispositions agree in all cases.
- Stale observation generation -> `YIELD_STALE`.
- Producer generation change -> `YIELD_PRODUCER`.
- Required predicate after deadline -> `YIELD_LATE`.
- Required UNKNOWN -> `YIELD_UNKNOWN`.
- NORMAL and IRRELEVANT_FALSE remain `READY_A`.
- Median candidate/global decision-time ratio: 0.2061706721.
- Median wait avoided in the two ready scenarios across three repetitions: 175.426273 ms.
- No OS-input authority: every row retains `authority=none`, `input_dispatched=false`.

These local wall times are descriptive fixture measurements, not production/model latency claims.

## Construction history

Construction01 failed before formal freeze because multiprocessing spawn startup contaminated the intended predicate evaluation clock. Construction02 switched only the fixture to asyncio and passed. A preformal source review found stale PLAN/test references; they were corrected and construction03 passed before the public freeze. All are preserved in the evidence capsule.

## Limits

Artificial delays may overstate production value. No live model, GUI/input, token saving, cancellation-compute saving, cross-platform timing, task success, runtime promotion or product claim. Correctness still depends on complete dependency declarations and valid generation/version state.
