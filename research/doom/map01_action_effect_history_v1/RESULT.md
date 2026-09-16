# MAP01 door action-effect history v1 — retained first outcome

## Disposition

- Formal first outcome: **`SUPPORT_ACTION_EFFECT_HISTORY`** under the preregistered numeric gates.
- Independent retained-evidence audit: **`HOLD_EVIDENCE_RETENTION`**.
- Promotion: **NO**. Do not treat v1 as independently replayable evidence for the history effect.

The experiment was frozen before formal measurement on GitHub (`run.py` commit `6c300d6c0f388944071a0e767bc978a1d76effd4`; prereg commit `320f959f079c2be12aeaa185cecf19619b6e8b92`). It used disjoint formal seeds `994100..994119`; development seeds were excluded.

## Formal result

Twenty fresh direct-ViZDoom MAP01 cases produced 320 retained current frames. The first 12 cases defined fixed opening/closing centroids; the final 8 cases were held out.

All eight held-out cases exposed a near-aliased opening/closing pair under the frozen current-view RMSE threshold `<= 0.005`. For these 16 alias observations:

- current-view-only accuracy: **0.500**;
- one-step visual delta/history accuracy: **1.000**;
- exact cross-label current-descriptor collisions across all formal samples: **4**;
- exact cross-label history-descriptor collisions: **0**.

Across the full held-out 128 samples rather than only the alias subset:

- current-view-only accuracy: **0.625**;
- one-step delta/history accuracy: **0.71875**.

The result therefore supports the narrow mechanism claim that temporal/action-effect evidence can disambiguate some task states whose current visual observation is ambiguous. It does **not** establish a useful long-horizon controller.

## Evidence-retention defect

The formal runner retained each measured current frame, but did not retain the immediate predecessor at the two measurement-window boundaries (`t0` before opening tic 1 and `t164` before closing tic 165). Every preregistered alias pair selected closing tic 165. Therefore the critical closing delta used during the formal calculation cannot be recomputed from retained PNGs.

The posthoc auditor verifies all 320 retained PNG identities, source/prereg hashes, current-view held-out accuracy, alias selection and alias current-view accuracy. It deliberately returns `HOLD_EVIDENCE_RETENTION` because alias-history accuracy cannot be independently reconstructed.

The v1 allocation is consumed. It must not be rerun or repaired in place. A successor may change **only retention instrumentation** by saving every measured frame's immediate predecessor under a new version/allocation while preserving seeds, classifier, thresholds and decision gates except for using a disjoint formal seed block.

## Scope

Direct ViZDoom teacher/evaluator mechanics only. No OS-input efficacy, model efficacy, MAP01 clear, general GUI improvement or causal long-horizon navigation claim.
