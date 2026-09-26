# #2494 same-route guard calibration — retained first outcome

Execution: **STOP_OUTER_EXECUTION_TIMEOUT**. Scientific disposition: **HOLD_NO_SAME_ROUTE_SUPPORT**. The prospectively frozen allocation completed 46/52 scheduled rows. Batches 0–2 completed 13/13 with Xvfb exit0. Batch3 retained 7 completed worker rows but no terminal BATCH.json/Xvfb-exit receipt before the outer tool envelope ended; six later rows were never started. The consumed batch was not rerun.

## H/T/D/C/U

- **H:** one fixed private-Tk route can estimate p, stale/fresh refusal cost and stale-action failure+recovery cost in one clock/population while keeping the independent stale oracle out of selector input.
- **T:** 48 primary episodes plus four right-censored controls, split calibration/evaluation; three fixed policies; exact source/schedule hashes frozen publicly before formal. Four immutable 13-row batches, no retry/replacement/tuning.
- **D:** formal PASS required all52 rows, all terminal/process evidence, nonzero held-out support, right-censor controls, raw-only audit and disjoint partitions. The unchanged auditor exits1 only for `row_count:46` and `schedule_ids`; no complete-row semantic error was reported. Because all four censor controls were among the six unstarted rows, the required censoring support is zero and PASS is prohibited.
- **C:** p=0.5 is an authored balanced route population, not deployment prevalence. REFUSE costs are actual read-only snapshot terminal intervals, not inferred from missing effects. c_f contains only independently observed wrong-B input followed by native recovery to A.
- **U:** no model/token measurement, cross-app transfer, natural stale rate, optimal guard threshold or calibrated reliability claim. Same-author raw audit is not external review.

## Retained complete-prefix measurements (descriptive only)

Calibration: p=0.500 (n=24), c_y_stale mean=0.440950 ms, c_y_fresh mean=0.390404 ms, c_f mean=96.343480 ms.

Evaluation prefix: p=0.500 (n=22), Wilson95=[0.3072210627372502, 0.6927789372627497]; c_y_stale mean=0.379803 ms bootstrap95=[0.36688375, 0.39256425]; c_y_fresh mean=0.429862 ms bootstrap95=[0.37676600000000005, 0.48295750000000004]; c_f mean=96.037233 ms (n=3) bootstrap95=[95.431807, 97.00234].

These values do not rescue the missing denominator and must not be cited as PASS_GUARD_POLICY_CALIBRATION_SCOPED.

## Construction and provenance

Construction-01 stopped on missing default Xauthority. Construction-02 exposed a real Tk binding mismatch: Control-a moved the cursor instead of selecting text, leaving the wrong-field value. Construction-03 passed after changing only the one-character native recovery recipe. Formal source/gates were then frozen (SHA256 c8f463081db4b0ae1439dac863d5ef4595e748cdabf7874eb6e70818701b2eb2) and committed/read back on Issue #2494 before formal execution.

The source and raw evidence are additive research only; no shared runtime behavior changes.
