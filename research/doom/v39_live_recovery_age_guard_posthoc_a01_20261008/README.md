# V39 A14 age-expiry confound posthoc (A01)

This offline posthoc asks whether the source-age rule masks health-boundary classification in the two retained A14 interruptions. It characterizes a guard decision, not the controller's live response.

The input cases are extracted from A14 decisions 2 and 5. Decision 2 observed health 79 (hard minimum 69) and ammo 43→42 at age 1524.789823 ms under a 1500 ms authored cap. Decision 5 observed health 53 (hard minimum 33) and ammo 41→39 at age 2133.932983 ms under a 2000 ms cap. Both retained outcomes classify health and ammo as `UNKNOWN/source_expired`. The same samples classified with a 30000 ms age cap produce `UNCHANGED` health and `SOFT_CHANGED` ammo. A synthesized health value one point below each frozen hard minimum produces `HARD_INVALIDATED` when expiry is isolated. When that below-floor value is paired with an expired age, the result is `UNKNOWN/source_expired`, while still requiring a new decision and refusing to keep the existing policy.

The A14 source report SHA-256 is `cf089fa6119f0ca6d2174adff9503cd0b200115d5d2f6255ee11f050b0a4d121`; its audit SHA-256 is `5977b0f67166448541910c37bccc54ef5bf93ceab04cfd19b7cce84ba8c2bd5a`. The frozen guard source is the current-main `research/live_control/observable_signal_guard_v2.py` at commit `08d3283f6d3c61cc6b032c6c9c5a63ec464c07ff`, SHA-256 `7be055c4bd68a1528f4b2b02b543435bd64465ea42d4452f5597d6dce08442a0`. Exact normalized inputs and hashes are in `INPUTS.json` and `FREEZE.json`; the original A14 files remain untouched.

## H/T/D/C/U

- **H:** At the retained source ages, an authored age cap takes precedence over health hard-boundary classification. A below-floor sample paired with an expired source remains fail-closed (`requires_new_decision=true`) even though its reason is classified as expiry. Under a diagnostic 30000 ms cap, the guard distinguishes unchanged/soft changes from a health hard crossing.
- **T:** Replay the two frozen input cases through the frozen current-main guard; compare authored cap, diagnostic cap, below-floor health with valid and expired ages. Include the exact-cap and +1 ns boundary. Two cases characterize these recorded examples, not a population rate.
- **D:** PASS if retained outcomes are both `UNKNOWN/source_expired`, diagnostic same-sample outcomes are health `UNCHANGED` and ammo `SOFT_CHANGED`, valid-age synthesized health crossings are `HARD_INVALIDATED`, and expired below-floor cases remain decision-requiring with no policy kept; FAIL otherwise.
- **C:** A different monitor sample could have occurred before expiry, and other implementation layers can affect delivery. The test isolates guard classification only. Extending the age cap may permit stale observations and is not a live recommendation.
- **U:** The synthetic crossed-and-expired case does not establish when a live HUD value became available or whether the crossing was current at the time of cancellation. No live threat-linked HUD timing, enemy attribution, cancellation latency distribution, safety, task effect, or efficacy is established. A14 remains an exploratory protocol-deviation run; no formal allocation is rerun.

## Reproduction

From this directory, run:

```powershell
python -B run_experiment.py
python -B -m unittest -v
python -B audit_result.py
```

`run_experiment.py` writes `RESULT.json`; the independent audit verifies the freeze hashes and recomputes expected classifications from `INPUTS.json`. The experiment has no GUI, planner, or game interaction.

## Consequence for the next live test

The next authorized live design should make source-age expiry a separately reported competing trigger and preserve exact source age, authored cap, sampled health/ammo, trigger reason, interruption/cancel ordering, release receipts, and the answer-admission outcome. It must not silently lengthen the cap to make a boundary crossing appear. A live threat/HUD crossing remains unverified and requires an authorized allocation.
