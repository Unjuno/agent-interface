# Integrated efficiency phase ledger v1 — retained result

Task: `INTEGRATED-EFFICIENCY-PHASE-LEDGER-20260917-001`  
Issue: #836  
Immutable BASE: `f9989b833611fb9cb8708007445b94a95d70c516`

Disposition: **`PASS_PHASE_LEDGER_RECONSTRUCTED_SCOPED`**.

The frozen container runner executed exactly once; formal reruns 0. The independent auditor passed every arm, phase, usage and count reconciliation. No model, GUI, provider, network or task-input action occurred in this allocation.

## Arm totals

| arm | input | cached subset | output | reasoning output | planner generations | model images | local observations | durable calls | phase-complete elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| plain | 63,128 | 0 | 754 | 306 | 7 | 6 | 105 | 36 | 62,754.198912 ms |
| ephemeral | 63,779 | 4,864 | 1,209 | 404 | 7 | 6 | 129 | 96 | 80,378.859099 ms |
| persistent | **26,563** | 0 | **472** | **127** | **3** | **2** | 136 | 114 | **51,627.109593 ms** |

Cached input is the provider-reported subset of input and is not added to or subtracted from the input-token total.

The retained persistent route is `cold, reuse, reuse, repair, reuse, reuse`. Its repeated-A and repeated-B phases require zero new model generation, model image, input/output token or reasoning-output token, while continuing to spend local observations and durable calls. Task 4's layout change uses one repair generation/image.

## Interpretation

The integrated path moves work rather than making all work disappear. In this retained allocation it reduces every measured model-visible count in the table versus both controls, but it increases local observations and durable calls. Therefore the result supports a narrower statement: **model-boundary/model-visible work is lower while local deterministic work is higher**. These units are not added into a synthetic scalar cost.

Global usage reconciles exactly to the retained audit: input 153,470; cached-input subset 4,864; output 2,435; reasoning output 837; 17 total model calls including three preflights; 14 image-grounding calls; 18/18 exact task rows; zero old-target pointer admissions.

RESULT SHA-256: `e79685ad94e0b3f5d7c15cb2341563209f5208cb0c553812dc7ba1b1e62e36b6`. Independent AUDIT SHA-256: `e57f7349dcb4988b8e0cd45b222d22693f320439a1ae7c6478e2ef99422a0002`.

This is a posthoc source-bound ledger for one retained Chromium allocation. It does not establish monetary cost, energy cost, population latency/reliability, human tempo, second-domain benefit or attribution to one submechanism.
