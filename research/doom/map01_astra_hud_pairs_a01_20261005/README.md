# Astra health-ROI pairwise replay — A01

## Scope

This is a deterministic posthoc pixel-separability probe over the exact 13 decision frames from the retained `map01-astra-attempt-v1` failure. It extends the adjacent-frame comparison in `analyze_map01_astra_failure_v1.py` to every ordered frame pair, including self-pair controls. It does not invoke a candidate, game, model, display server, or input path.

## H / T / D / C / U

- **H:** On this one frozen trajectory, the existing one-way health-ROI guard invalidates exactly when the manually transcribed HUD health label differs between any two decision frames.
- **T:** For all `13 × 13 = 169` ordered pairs, apply the exact guard source and the existing `[440,585,535,635]`, RGB threshold `32`, and `100` changed-pixel settings. Compare `INVALIDATED` against the source/target manual health-label inequality. Self-pairs are controls. Unit tests cover ROI localization and positive/negative outcomes.
- **D:** `PASS_SCOPED` only if all 169 pairs match the label inequality and preserve the guard’s no-authority/no-success guarantees; any mismatch is `FAIL_MISMATCH`.
- **C:** The detector measures pixel change, not health semantics. The labels were manually read from this same run; all frame pairs are dependent, and nonadjacent pairs discard temporal order.
- **U:** One episode and 13 decision frames cannot estimate live false-positive/negative rates, sampling-delay behavior, or response latency. Health change does not identify threat cause, direction, task effect, or a safe next action. A live threat-exposure allocation remains separately required and unassigned.

## Reproduction

From repository root:

```powershell
python -m unittest discover -s research/doom/map01_astra_hud_pairs_a01_20261005 -p test_pairwise_probe.py -v
python research/doom/map01_astra_hud_pairs_a01_20261005/pairwise_probe.py
python -m py_compile research/doom/map01_astra_hud_pairs_a01_20261005/pairwise_probe.py research/doom/map01_astra_hud_pairs_a01_20261005/test_pairwise_probe.py
```

`FREEZE.json` binds the base main SHA, report, frame manifest, existing manual transcription, all 13 frame bytes, exact guard/analyzer source, candidate, test, and this protocol before the corpus run. `pairs.jsonl` retains every pair-level outcome; `RESULT.json` is the compact disposition.

## Result interpretation

Even a scoped pass establishes only that this configured guard separates these manually labeled health states across the retained still frames. It does not validate fresh-sample acquisition, temporal/source binding under a running session, health extraction, policy relevance, threat response, recovery, physical release, or MAP01 success. The existing live gate stays open.
