# MAP01 guarded continuation after visible ammunition cue

This exploratory caller composes #9896's fixed HUD templates with a fresh X11 window review, stale-reference refusal, and an explicitly preplanned short subsequent attack. It is not model-selected behavior or a production recovery implementation. After a held attack is cancelled and released, a bounded visual review compares the HUD with exact 50/49 templates. Only `visual_49` proceeds: the caller reviews the same window, checks that the old `game` alias is refused without input, obtains a fresh observation and alias, and verifies the same 49 crop and window binding before admission, focus and key press. A 500 ms cooperative review timeout or unrecognized crop produces no continuation. The visual cue does not settle the original action's semantic effect, establish a hit, or automatically authorize repeating an arbitrary user action; the follow-up attack is preauthorized specifically for this isolated test. An exact crop can be forged and the final check-to-input boundary is not atomic.

| Run | Input / planned follow-up | Visual decision | Review / old alias | Follow-up | Evaluator final ammo |
| --- | --- | --- | --- | --- | --- |
| w01 | no input / fire | timeout_unknown | not attempted | none | 50 |
| w02 | cancel / fire | visual_49 | reviewed / refused | completed, release verified | 48 |
| w03 | overlay / fire | unrecognized_unknown | not attempted | none | 50 |
| w04 | cancel / withhold | visual_49 | reviewed / refused | deliberately withheld | 49 |
| w05 | cancel / fire | visual_49 | reviewed / refused | completed, release verified | 48 |
| w06 | no input / fire | timeout_unknown | not attempted | none | 50 |

All three cancellation runs verified held input, cancellation request, interrupted wait, and empty release while preserving partial effect unknown. For the two completed continuations, audit reconstructs the 49 crop from the actual full-screen observation artifact at each recorded guard stage, including before `f` down, and checks bindings and verified release. The final ammo differences are evaluator observations, not the controller's input or proof of hit, kill, causal efficacy, or MAP01 completion. The controls differ in timing and live state; this small fixed-order, same-seed sample is not a performance or reliability estimate.

Each run used a fresh WSLc container, private Xvfb, Freedoom2 MAP01 ASYNC_SPECTATOR at 35 tics/s, skill 1, seed 991031, no network, one CPU, 1 GiB, and image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25. Templates come from #9893 and were fixed in #9896 before this series. Main was 8deadc03fcee8c8636ae6cbf66874fb0e18d99af; mounted Python runtime matched 6a9c787d2caf9740612de65bd2539846dd87cad4 in #9891 and subsequent commits were research-only. The deadline is cooperative and does not bound a blocked capture. ZIPs retain all source, conditions, screenshots, telemetry, guarded review and receipts. `python audit.py` verifies the six attempts, templates, crop checks, controls, stale refusal, input emissions and release.
