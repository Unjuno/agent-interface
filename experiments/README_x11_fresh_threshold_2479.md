# X11 fresh-family threshold sweep (#2479)

This is a research-only reproduction harness. It does not change runtime policy or promote a threshold.

## Inputs

Place the retained local datasets beside the script:

- `shiftout/manifest.json` and referenced raw frames
- `freshout/manifest.json` and referenced raw frames

The script uses the same fixed split and seed recorded in Issue #2479. It reports classification accuracy and routing counts for positive-confidence thresholds. A positive prediction is required before an item can be accepted.

## Reproduction

For deterministic CUDA, set `CUBLAS_WORKSPACE_CONFIG=:4096:8` before starting Python. Set `X11_SWEEP_CPU=1` to run the CPU comparison.

This harness is intentionally not a production adapter and makes no generalization claim.
