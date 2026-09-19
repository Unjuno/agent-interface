# #1565 matched temporal-sheet prediction Rung1

Task: `TEMPORAL-SHEET-MATCHED-PREDICTION-R1-20260918-001`
Base: `91bf60f8d2f4a46e44bb29dcf69f9168fee52dee`
Parents: #1525, #746, #1550.

## H
With exact source frames held fixed, one packed temporal sheet can preserve dynamics-prediction value relative to the same four images supplied separately, while potentially changing provider-visible image cost/latency. History value and packing value are separate estimands.

## T
Construction is model-free. Six deterministic 320x250 RGB histories are generated. `SEPARATE_FRAMES_4` uses the exact four chronological source images; `PACKED_SHEET_4` is exact 2x2 row-major concatenation at 640x500 with no resize/crop/overlay/gutter, so both history arms contain exactly 320,000 pixels. `CURRENT_ONLY` is exact source frame4.

Ground-truth motion/future-region is generated from hidden fixture parameters and is absent from the model prompt. Construction verifies raw/PNG hashes, quadrant reconstruction, source/timestamp/role identity, equal pixel budget and fail-closed corruptions. A later model allocation requires a separate grant.

## D
Construction PASS only with exact source/quadrant/current/budget/oracle/role integrity, independent audit and all corruption controls. Model promotion later requires PACKED non-worse correctness vs SEPARATE plus at least one strict preregistered correctness/cost/wall benefit without worse static/reversal controls. CURRENT_ONLY is reported separately.

## C
Provider image preprocessing may itself create a presentation effect; simple synthetic motion may saturate; four separate images may encode order differently; image count does not imply token count; local tracking remains a competing architecture.

## U
Construction proves only matched presentation mechanics. No model efficacy, token, latency, GUI, action or human-tempo claim.
