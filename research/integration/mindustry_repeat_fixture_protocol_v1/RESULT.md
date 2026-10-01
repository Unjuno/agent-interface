# Mindustry repeat fixture protocol v1 — retained first outcome

Task: `MINDUSTRY-REPEAT-FIXTURE-PROTOCOL-20260917-001`  
Issue: #868  
Immutable BASE: `c833289b3a632c69087e8b51209f92a8eddda707`

Disposition: **`PASS_MINDUSTRY_REPEAT_FIXTURE_PROTOCOL_SCOPED`**.

The source-first frozen disposable-container formal runner was invoked exactly once; formal reruns were zero. Independent audit passed with no errors and four structured corruption controls were all rejected. No provider/model call, GUI, Mindustry process, X11 input, network task action or user-data action occurred.

## Candidate protocol closed by this rung

The candidate keeps benchmark checkpoint/reset authority off the controller operation set. Controller operations remain `submit`, `clock`, and `cancel`; `checkpoint`, `score`, `reset`, and `geometry_mutation` are benchmark-private.

The frozen good trace enforces, for each of A1/A2/A3/B1/B2/B3:

`task_ready -> checkpoint_snapshot -> score_verified -> reset_applied -> reset_witness -> next task_ready`

After A3, exactly one `geometry_mutation(A->B)` occurs after A3 reset witness and before B1 ready.

The candidate mod source resets only the semantic task target and resource consumed by a previously VERIFIED task:

- target tile `(137,52)` -> `Blocks.air`;
- core copper -> `canonicalCopper` with `ItemModule.set(Item,int)` semantics.

The reset branch is gated by both the `awaitReset` phase and a benchmark-private `score-pass-N.receipt`. A failed score moves to a failed phase and exposes no reset/next-task path.

## Negative controls

The frozen protocol rejects reset-before-score, reset after failed score, next-ready before reset witness, controller checkpoint/reset attempts, non-monotonic epoch, bad reset witness, duplicate checkpoint, and duplicate reset. Controller projection contains no private checkpoint/score/reset/geometry events.

Corruption controls independently mutate the retained result to inject reset-before-score ordering, a control-plane leak, removal of the A->B geometry event, and formal-count mutation. The independent auditor rejects all four.

## Integrity

- formal invocation: 1; reruns: 0;
- source-first freeze commit: `b7fce8912465184280a7e37c16703f314a6e2f19`;
- predecessor #863 RESULT blob: `ae4d6143370117c2c3655e61ed62a570060d55b2`;
- retained real resize backend blob: `e09be2a5acc5e746acab262504ca0ef27fc757b5`;
- upstream ItemModule source blob: `59e068a3bf9e430a524c4e87da6b8947fc54fb8f`;
- RESULT SHA-256: `0dabfca6a7fb6495cebe5b8910d42286ba93581d50676fff701987a637cc8c73`;
- AUDIT SHA-256: `3f1a1259a506d9912f23aeb9f12de6ad522e6c92334305dc1c163bcd2d7cb664`;
- CORRUPTION SHA-256: `bc8d42af2a8049ec1af0b332f3d3692869c54acb1fd3f023463f779ff87e29c1`.

## Interpretation / boundary

This source-closes the smallest in-process benchmark control protocol needed before a live Mindustry repeat-workload smoke. It reuses the previously retained X11 resize mechanism rather than inventing another geometry layer, and it keeps benchmark reset/oracle data outside the controller channel.

It does **not** prove actual Mindustry engine execution of the candidate mod, reset latency, real A->B geometry/handle invalidation in the six-task workload, or any provider token/wall-time benefit. The next high-information step is one bounded live fixture smoke/transfer under an explicit live/GUI lease. If that passes, the final #57 plain/current-optimized/persistent model allocation can be preregistered; no further synthetic mechanism is currently justified.
