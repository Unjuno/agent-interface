# Mindustry repeat/reset contract v1

Task `MINDUSTRY-REPEAT-RESET-CONTRACT-20260917-001`, Issue #863, base `b9dcc5cc456b95ed97d36276ec5557bcae1cad5d`.

H: benchmark-owned reset after independent task scoring can make the existing one-tile task repeatable without laundering wrong task effects or leaking engine/oracle state.

T: exact current single-tile scorer semantics over A1/A2/A3/B1/B2/B3. Each task is scored before reset. Reset separately restores exact canonical guard/source/core/copper/paused state with monotonic epoch. Controller-visible projection contains only task ID/text/layout/epoch.

D: PASS only for 6/6 verified effects, 6/6 verified resets, exact A/A/A/B/B/B order, fail-closed reset/effect/leak controls, one formal invocation, zero reruns, independent audit agreement.

C/U: deterministic benchmark contract only. No live reset, GUI geometry mutation, model call, token saving, latency, or persistent-handle result follows.
