# MAP01 OS rolling action-effect history v4 — retained result

## Decision

**`PASS_ROLLING_HISTORY_TRANSFER` + `PASS_AUDIT`.**

This is the source-first successor to the stopped v2/v3 rolling attempts and to the earlier on-demand OS history failure. It changes acquisition architecture only: short visual history is retained continuously, decisions bind only to a 50–100 ms pair, and among admissible pairs the newest current frame is selected first. The classifier, fixed initial-door task, 500 ms freshness gate, semantic programs, release path and calibration remain unchanged.

## Formal block

Sixteen fresh private X11/Freedoom MAP01 cases, seeds `996400..996403`: opening/closing × current/history, alternating order. No model calls, automap, controller-visible engine position/angle, pause/save-state or direct game action vectors. Harness-only `POSITION_X` scores door transit.

Independent raw audit result:

- history semantic action correct: **8/8**;
- history door transit: **8/8**;
- history condition success: **8/8**;
- history stale yields: **0**;
- history release failures: **0**;
- current semantic action correct: **1/8**;
- current condition success: **1/8**;
- current-view opening/closing alias exposure: **8/8** matched pairs at RMSE <= 0.001;
- temporal binding failures: **0**;
- median history controller-start observation age: **235.532 ms**;
- median current controller-start observation age: **257.580 ms**;
- median retained pair gap: history **69.806 ms**, current **70.014 ms**.

The audit re-decodes every retained previous/current PNG, verifies RGB hashes, reconstructs the fixed descriptors and predictions, verifies every selected pair against the rolling timestamp ledger, independently checks that the selected current frame is the freshest temporally admissible frame, recomputes alias exposure, and rechecks all release records.

## Predecessor failures preserved

- v2: stopped after 5/16 because nearest-gap selection admitted a 35.873 ms pair outside the intended history horizon. `ABORT_HARNESS_TEMPORAL_BINDING_CONTRACT`.
- v3: stopped after 3/16 because target-gap closeness outranked recency; a closing/history case selected an old admissible pair and correctly yielded at 613.138 ms age. `ABORT_PAIR_FRESHNESS_PRIORITY`.

Neither partial block is pooled into v4.

## Interpretation

This supports a narrow general mechanism: **when a decision may need short action/effect history, keep a bounded rolling history continuously and bind execution to the freshest already-retained evidence satisfying the temporal contract.** Do not synchronously acquire the extra history only after the decision asks for it, and do not optimize history-horizon fit ahead of evidence freshness.

The result is still a short initial-door task. It does not establish MAP01 clear, long-horizon navigation, model efficacy, human-level reaction, or general GUI improvement. A direct matched on-demand-vs-rolling acquisition study is the next causal architecture test.
