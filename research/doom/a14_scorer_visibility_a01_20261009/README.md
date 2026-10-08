# A14 scorer visibility and signal scope audit

This additive posthoc analysis addresses an unresolved #59 measurement question: did the independent progress scorer provide information to the controller during A14's model-pending cover intervals?

## H/T/D/C/U

- **H:** The retained scorer sampled terminal/progress flags but was not connected to the controller and did not measure the threat/damage signals needed to judge an active cover.
- **T:** Recompute visibility, event count, distinct sampled state, payload fields, and sample cadence from A14's retained raw scorer samples, summary, terminal score, and event stream. Verify each raw input's SHA-256 and preserve A14's existing exploratory-protocol-deviation classification.
- **D:** PASS for the narrow audit only if the four pinned raw hashes match, all samples are included, controller visibility and event counts are recomputed, and the result does not infer a static or threat-free scene from zero events.
- **C:** The scorer may have sampled genuine terminal/progress state, but a state that stayed constant in its narrow payload could coexist with unseen threats, health changes, or actionable images.
- **U:** This is posthoc analysis of an exploratory run. It does not show what a connected scorer or controller would observe, establish useful feedback or control efficacy, or replace the required fresh live threat-exposure allocation.

## Result

The raw record contains 1,519 samples. All 1,519 say `controller_visible=false`; the scorer emitted zero events; its payload contains only death/kill/map-exit/episode-finished/player-dead flags plus sample time and schema. Those flags occupy one distinct state in the retained samples. No health, ammo, enemy identity, or image evidence is in the scorer payload. Therefore zero scorer events means **no event was emitted by this isolated scorer**; it does not mean the game scene was static or threat-free.

## Reproduction

From the repository root:

```powershell
python research/doom/a14_scorer_visibility_a01_20261009/analyze.py
python -O research/doom/a14_scorer_visibility_a01_20261009/analyze.py
python research/doom/a14_scorer_visibility_a01_20261009/audit.py
```

The analyzer writes `result.json`; the auditor independently reconstructs the metrics from the four SHA-pinned A14 raw files and checks the scope statement. No game, model, GUI, input, or container is started.
