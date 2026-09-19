# Successor #1999: isolate model-facing visual cues

## H/T/D/C/U

- **H**: At least one low-complexity cue may improve multimodal target localization without increasing false-target selection.
- **T**: Four uncombined arms (`RAW`, `BORDER_RULER`, `COARSE_GRID`, `TARGET_CONTEXT_CROP`) over small, repeated, edge, and target-absent source families.
- **D**: Deterministic standard-library source-coordinate fixture; independent coordinate-map and raw-fallback checks precede any model call.
- **C**: Identical source dimensions and target truth; no live click or mutation; target-absent remains abstention; raw evidence remains authoritative.
- **U**: No multimodal model endpoint is available in this run, so cue utility, false-target rate, response cost, and localization accuracy are not measured.

## Disposition

`HOLD_MODEL_EVALUATION_UNAVAILABLE`: 16 cue/family rows were constructed with zero mapping failures and zero GUI/model calls. This is not a cue-performance result and does not promote any arm.
