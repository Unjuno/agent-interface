# TEMPORAL-SPECULATION-FRESH-REVERSAL-GATE-20260918-001

## H
Given the retained #1134/#1194 boundary that current+history evidence is outcome-aliased, a continuation policy that waits for exactly one fresh post-current directional observation can preserve continuation on non-reversal traces and deterministically YIELD on reversal traces, while immediate continuation from the aliased current state cannot do both.

## T
Container-only deterministic composition; no X11/model/provider/task input/network/shared runtime.
Freeze the #1134 logical projection: side L/R; history->current direction +/-1; first post-current direction +/-1; mode is evaluator-only.
Compare one factor:
- IMMEDIATE_CONTINUE: continue from the pre-future aliased state.
- ONE_FRESH_DIRECTION_GATE: after one fresh post-current observation, CONTINUE iff fresh direction equals retained history direction; otherwise YIELD_REVERSAL.

Primary corpus: exact logical 64-row shape from #1134 (16 CONTINUE pairs +16 REVERSE pairs x L/R) plus 250,000 seeded nuisance-metadata cases that preserve the same directional semantics. Independent oracle is separately implemented and never calls candidate code.

## D
PASS_FRESH_REVERSAL_GATE_SCOPED iff:
- candidate/oracle mismatch0;
- all 32 retained-shape CONTINUE rows continue;
- all 32 retained-shape REVERSE rows YIELD_REVERSAL;
- immediate baseline has 32 reversal misses on the retained-shape rows;
- fresh sample never grants authority/task input;
- missing/zero/malformed fresh direction fails closed to YIELD/UNKNOWN;
- source/result/audit integrity passes; primary invocation1/reruns0.

## C
The #1134 fixture authors a clean one-step reversal and its first post-current sample fully reveals the direction. Real tasks may reverse between samples, oscillate, contain noisy tracking, or require richer features. The experiment does not measure how long obtaining the fresh sample takes or whether waiting is useful end-to-end.

## U / stop
This is a deterministic contract-composition result only. No new X11 collection, model benefit, planner-gap latency, task effect, token saving, or live authority claim. Stop after one source-first construction/audit. Any latency/value question requires a separate retained/live rung.
