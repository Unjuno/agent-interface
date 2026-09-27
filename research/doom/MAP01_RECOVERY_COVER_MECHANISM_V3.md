# MAP01 bounded-recovery mechanism v3

Status: **FROZEN BEFORE FIRST FORMAL RUN.**

Allocation: `map01-recovery-cover-mechanism-live-v3-01`  
Base: `ff2bbb5e200e2bf8ee2295ad97ca9dd0f158a371`

## Why this is a separate experiment

The older matched-v2 preregistration mixed a `same_model` efficacy requirement with a zero-model mechanism runner. That combination is not valid. V3 explicitly tests only the causal local-continuation mechanism under a frozen 600 ms simulated planner delay.

The evidence chain is now strong enough for this narrower formal block:

- protocol-valid real MAP01 measurement live-04 passed at `1cceae7c`;
- real MAP01 recovery development v2 passed and was retained at `9e6d5ecd`;
- the source-only three-pair matched runner was integrated at `120a1b8d`;
- workflow-path-global one-shot ownership is retained from `fdfdd282`.

No frontier model is invoked in v3. A PASS cannot be quoted as frontier-model efficacy.

## Frozen block

Three counterbalanced pairs all reload the same `map01-threat-contact-v2` fixture (seed 990619). Every arm first executes the same 180 ms `d` prelude and observes fresh state.

- Coast: 600 ms input-free coast.
- Recovery: reuse the preceding `d` intent as five 50 ms pulses separated by observations, with a 400 ms authority lease, 1000 ms source-age ceiling, fresh-sequence requirement, observed-health requirement and fail-closed cancellation on any health loss.

Retained input is measured from `input_admission` and verified `input_release_transition`, intersected with the planner-wait window. Independent scorer state stays controller-invisible.

## H / T / D / C / U

**H.** Explicitly admitted, source-guarded reuse of the previous motor intent reduces input-free planner-wait time in the fixed real MAP01 threat state without release/scorer failure or a negative independent recovery event.

**T.** One allocation, three counterbalanced coast/recovery pairs, fixed fixture/seed, zero model calls, direct retained-input timing, six terminal-score audits, workflow-path-global launch ownership. No retry.

**D.** `PASS_MECHANISM_ONLY` requires continuity improvement in all 3 pairs, paired median no-input-upper reduction at least 10%, zero independent negative recovery events, zero hard runner failures, six terminal-score agreements, verified release, zero missed scorer periods and zero scorer leaks. Safe but weaker continuity is `HOLD`. Hard safety/measurement failure or a negative recovery event is `FAIL`.

**C.** Repeating the previous `d` direction may merely move the avatar without useful task effect, may be harmful under threat, or may be cancelled immediately by the health guard. The sparse scorer may observe no positive event even when continuity increases.

**U.** This is one fixture and a simulated 600 ms planner delay. It does not estimate frontier-model quality, token cost, general MAP01 completion, or human-tempo performance. Positive scorer evidence is retained descriptively and does not expand claim scope.

## Release interpretation

A PASS supports the narrow statement that the guarded runtime can reduce measured idle control time on real MAP01 while preserving the measured safety boundaries. It does not support “the model plays DOOM better” or “human-speed control.”
