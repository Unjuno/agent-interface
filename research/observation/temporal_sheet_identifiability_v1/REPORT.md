# #1550 retained temporal-sheet packing identifiability result

Decision: **`PASS_RETAINED_TEMPORAL_SHEET_BENEFIT_NOT_IDENTIFIABLE_SCOPED`**.

The repository already implements #1525's basic primitive. Current retained DOOM controllers v31/v32/v38/v39 all contain the same `temporal_sheet` body: four recent game-window sources are cropped/resized and packed into a numbered 2x2 `642x502` model image. Retained model runs refer to these images as `temporal-sheet.png`.

## Retained families inspected

Seven model-facing report families were pinned by Git blob and first model-image/session metadata:

- MAP01 v31 soft context;
- v32 final admission;
- v38 integrated threat;
- v39 coast liveness;
- stagnation baseline;
- stagnation candidate;
- effect-receipt long baseline.

Every inspected family uses the **packed temporal sheet** presentation. Repository search found many packed-sheet uses, but no matched `separate_frames` arm and no current-only arm suitable for isolating the *packing* effect within the bounded search scope.

## Candidate-pair audit

Four tempting comparisons were normalized. Admissible presentation-only pairs: **0/4**.

The strongest near-match is v31 decision0 versus v32 decision0:

- model: `gpt-5.6-luna` / `gpt-5.6-luna`;
- effort: low / low;
- packed model-image SHA-256: identical `bb7855e2...`;
- presentation: packed temporal sheet / packed temporal sheet;
- model session IDs: different;
- prompt/schema/task-oracle matchedness: not established.

This pair can support that the same packed bytes were reused across two runs, but it cannot estimate a packing effect because the presentation does not differ.

v38/v39, stagnation baseline/candidate, and stagnation/effect-receipt comparisons are still weaker: packed images differ, sessions differ, and the presentation remains the same.

## Background evidence kept separate

- #752 `PASS_AGE_TARGETED_TEMPORAL_SAMPLING_SCOPED` is model-free representation-timing evidence.
- #808 `HOLD_NO_PREDICTION_GAIN` is a deterministic local-predictor result, not frontier-model evidence.

Neither is converted into evidence that a spatial sheet helps Astra/Luna.

## Integrity

One deterministic retained-data invocation; reruns/replacements/tuning `0/0/0`.

Primary audit:
- families 7;
- candidate pairs 4;
- admissible pairs 0;
- errors `[]`;
- corruption controls 5/5 PASS.

Independently structured audit recomputed the same admissible-pair count `0`, errors `[]`.

Local SHA-256 before publication:
- `ledger.json`: `1da7f670d7c3ad04d33dba4a24d8feb4b2fdf36dcd632a8112787663f0bfc893`
- `audit.py`: `14bca8a3b3cbc15ca82579853c45a772be4762922a65fc352edd5bc2e01d13f6`
- `independent_audit.py`: `82b5a631a54c26bf48c91c4bf995b6fd3535319c27524bed525ee704dc413a62`
- `AUDIT.json`: `c5811a50a24ccebd87e5e574a725c90fed95fef07f45d62f483af0f2d07c5f9f`
- `INDEPENDENT_AUDIT.json`: `682beeec1bea177af77b4d4364c54c81f041c9147954409aa68701dabeac5d55`

## Interpretation

This is **not** evidence that temporal contact sheets are ineffective. It is evidence that the retained corpus cannot causally separate `history exists` from `history is packed spatially` or isolate packing from controller/session/task changes.

The next legitimate model-facing rung, if allocated, should be prediction-only and hold the exact source frames fixed across:

1. `CURRENT_ONLY` — history-benefit baseline;
2. `SEPARATE_FRAMES_N` — same history images as separate model inputs;
3. `PACKED_SHEET_N` — the exact same source images packed into one sheet.

For the packing question, the decisive comparison is (2) vs (3), with the same prompt/schema/model/effort/session policy and independent future-state oracle. Include static and abrupt-reversal controls. No task input should be added until prediction value is established.
