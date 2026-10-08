# XTerm event-source timing transfer — first outcome

Decision: `HOLD_XTERM_EVENT_SOURCE_TAIL`.

One source-first formal invocation; reruns0.64 matched pairs /128 fresh native XTerm transactions ran on one fresh private Xvfb/Openbox allocation. Both arms used the same persistent planner stub, XTEST Return20ms hold, app-owned exact-token effect and final independent process/effect/empty-key scorer. The instrumented arm additionally acquired keymap input ack, full-root XGetImage observation, first-effect file polling and the complete seven-role #1176 timing envelope.

## Frozen formal decision

- effects correct:128/128; instrumented gates:64/64; forbidden promotions0;
- baseline wall p50 **234.980ms**, p95 **285.166ms**;
- instrumented wall p50 **215.832ms**, p95 **266.451ms**;
- paired instrumented-minus-baseline p50 **-19.232ms**, p95 **31.401ms**;
- active event-source acquisition p50 **8.479ms**, p95 **9.521ms**.

The frozen PASS required paired p50<2ms, paired p95<10ms and acquisition p95<10ms. Acquisition passes, and paired median is below2ms because it is negative, but paired p95 **31.401ms** fails the10ms tail gate. Therefore the retained outcome is HOLD, not PASS. Negative paired values do not mean instrumentation accelerates XTerm; termination scheduling differs between fresh arms and is not a causal speedup estimate.

## Postformal localization (descriptive only)

The HOLD decision was not changed. Active acquisition p95 decomposes to:
- X keymap down probe **0.081ms**;
- full-root 640x360 XGetImage+SHA **8.834ms**;
- effect-file poll active time **0.358ms**;
- terminal scorer active work **0.417ms**;
- typed JSON serialize **0.105ms**; typed gate **0.020ms**.

Thus the online acquisition budget is dominated by the deliberately conservative full-root screenshot, while the ~31ms paired wall p95 tail persists in both counterbalanced order strata and is attributed to native XTerm/Openbox process/termination scheduling rather than the typed gate itself.

## Integrity

- RESULT SHA-256 `175cae41bdf399ffec584cdc841633cdce01139ebdab3954fb1253efb99497dc`;
- exact 64-pair rows SHA-256 `ae6386be3fe95358f819952b775139d6c189a29af8eacb2aeab4da9656359810`; compressed rows SHA-256 `0b9ea733acbe8bf5b0be5e768d1c46f76e4180d39a572877c386e6f07a4d5021`;
- independent audit PASS/errors[]; corruption controls5/5 reject; source rehash11/11 exact; invocation1/reruns0.

## Boundary / next discriminator

This does not establish a general XTerm instrumentation cost PASS because the frozen controller-wall tail gate failed. The clean next one-factor experiment is **observation source size**: hold XTerm/action/effect/timing semantics fixed and replace the full 640x360 root sample with a bounded target-window/ROI sample. Do not change the wall-tail threshold in that successor. Separately, XTerm termination jitter should remain a competing explanation rather than being hidden by redefining the endpoint after the result.
