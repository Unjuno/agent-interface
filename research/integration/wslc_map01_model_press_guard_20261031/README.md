# Model-selected MAP01 action with pre-press image checks

Four fresh WSLc allocations follow the development-selected Freedoom2 MAP01 route in `wslc_freedoom_map01_threat_route_20261031/e07.zip`. Each sends a synthetic game screenshot to a prestarted `gpt-6.1-sol` low session, which returns a structured fire/idle policy, target point and duration. After checking the first and current target patches, the caller starts a second model turn. If the first policy selected fire and passed the check, a bounded local attack can run while the second turn is pending. Game labels and state are evaluation-only and are not given to the model or used by the policy.

This follow-up to PR #9884 adds a geometric center bound and repeats the exact 8×8 patch/binding check inside the existing guarded-input callback, including immediately before the key press. In the injected arm, the test maps a small magenta X11 window over the model-selected point after the initial check and before input. It does not affect the screenshot sent to the second model. All four attempts were planned together; no allocation was replayed or omitted.

| Run | Condition | First model policy | Initial check | Input boundary | Game kill delta |
| --- | --- | --- | --- | --- | ---: |
| h01 | normal | fire 500 ms | accepted | before-key check accepted; fire completed | 1 |
| h02 | injected overlay | fire 500 ms | accepted | before-admission check rejected; no input dispatched | 0 |
| h03 | injected planned | fire 500 ms | changed patch; rejected | no overlay or fire attempted | 0 |
| h04 | normal | fire 500 ms | accepted | before-key check accepted; fire completed | 1 |

In h01 and h04 the game-reported kill count increased while the caller was still polling for the second model result, and the attack key and all preceding inputs were released. Model-selected durations were used; the selected target point was checked but not used to aim, so attacks followed the existing game crosshair. Both normal runs and both controls had no health loss. In h02 the locally injected overlay changed the inspected patch and the existing additional guard refused before admission, with `input_dispatched=false`; h03 is a separate earlier safe stop, not a successful overlay test. This is one positive and one negative mechanism demonstrated twice/once respectively, not a reliability estimate or proof of causality for the game kill. The game engine itself supplies labels and kill count.

The callback narrows the time between image validation and key press but does not make capture and emission atomic. Identical pixels do not prove object identity, model correctness or a clear line of fire; the center bound is geometric rather than a hostile classifier. Exact matching may reject harmless animation, as h03 shows. File markers bound the caller's observed model-call interval but are not synchronized provider-side timing. The route was discovered through prior exploration, order was fixed, and these tests do not establish damage reduction, the v39 policy, repeated recovery, model autonomy or MAP01 completion.

The archives retain conditions, schema, prompts, model results/usage, synthetic images, input/close receipts, every callback observation and game telemetry. Nested private model protocol journals remain local and are represented by hashes and size. `python audit.py` checks all four, independently crops the captured PNGs at each callback, associates model turns and usage, verifies input release and observed event ordering, and preserves the ineligible h03 attempt.
