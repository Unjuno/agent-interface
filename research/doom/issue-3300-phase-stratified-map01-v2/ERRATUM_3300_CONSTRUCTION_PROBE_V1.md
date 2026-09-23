# Erratum: issue-3300-obstac-async-phase-probe-v1 scope

Added 2026-09-20 after re-auditing the merged raw JSONL. This supplements the immutable construction result; it does not replace or rewrite it.

## Corrected finding

The earlier result text describes the probe as running against an “advancing ViZDoom episode.” That wording is not supported by the raw evidence. Recomputing `results/construction-01/raw.jsonl` yields 36 rows, 108 outer scorer calls, all retained tic values equal to 14, and zero observed tic transitions across all strata. The runner starts `ASYNC_PLAYER` and `new_episode()` but never calls `advance_action`; under this container setup the episode remained static.

Therefore the retained `PASS_CONSTRUCTION_AUDIT` proves only that the exact `_coherent_progress_sample` predicate executed, its read pairs and outer-call spans were retained, and an independent same-tic decision audit passed on a static episode. It is not evidence about live asynchronous coherence, phase offsets, boundary-crossing probability, or engine progress under an advancing MAP01 episode. Issue #3300 remains `HOLD_LIVE_SPAN_UNIDENTIFIED`.

The independent fact is reproducible from the retained artifact: raw SHA-256 `bfa27da03e259af1c48da367cd688e301c932abf27263ce10345282a50d02b33`; observed tic set `{14}`. No attempt count, threshold, source code, or historical raw row was changed.

## H/T/D/C/U

- H: verify whether the previously reported construction probe exercised a changing game clock.
- T: re-read and independently aggregate the merged raw JSONL and runner source at the recorded PR head.
- D: raw hashes and counts above; all three stratum final-tic sets equal `{14}`.
- C: retract the “advancing episode” interpretation; retain PASS only for static-predicate execution and trace-audit mechanics. No live-coherence claim.
- U: formal #3300 work still requires a predeclared clock-driving mechanism compatible with the frozen MAP01 action policy and observable from a separate scorer thread. The exact private-fixture no-input diagnostic is retained separately in `SETUP_DIAGNOSTIC_20260920.md`.
