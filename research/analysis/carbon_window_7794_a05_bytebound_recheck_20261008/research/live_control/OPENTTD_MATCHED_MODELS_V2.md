# OpenTTD matched model-route replication

Status: two descriptive blocks; fixed Astra is the next candidate, not promoted.

The second preregistered block reversed the endpoint arms from the first block:
adaptive, fixed Astra, then fixed Luna. Astra remained in the middle, so this is
not a complete counterbalance. Every arm again used the same canonical save,
task, initial geometry, proposal schema, prompt policy, nine-turn limit and
independent engine evaluator. No arm was retried.

## Second block

| Arm | Hard result | Turns | Initial observation to semantic completion | Model wait | Proposal to useful feedback | Input tokens | Exact frames | Durable calls |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Adaptive, 2 Luna then Astra | FAIL | 7 | unavailable | 71.934 s | 14.305 s | 109,397 | 36 | 24 |
| Fixed Astra-medium | PASS | 7 | 94.929 s ±50 ms | 82.477 s | 10.338 s | 113,724 | 28 | 24 |
| Fixed Luna-low | FAIL | 9 | unavailable | 92.342 s | 28.403 s | 125,515 | 65 | 36 |

Fixed Astra again passed target ownership, bidirectional connectivity, the clear
forbidden row and unchanged surroundings. Fixed Luna again reached the turn
limit without completing the road.

The adaptive arm exposed a stronger failure. After six action turns it visually
declared the road complete. The independent engine evaluator found target roads
and connectivity absent and surrounding tiles 613, 614 and 615 changed. Thus a
plausible final screenshot and model `road_visible=true` were insufficient
completion evidence.

## Two-block evidence

| Arm | Hard successes | Observed successful completion times | Interpretation |
| --- | ---: | --- | --- |
| Fixed Astra | 2/2 | 98.351 s; 94.929 s | Replication candidate; mean 96.640 s across only two episodes |
| Adaptive | 1/2 | 100.201 s; one false visual completion | Authored two-turn switch is not promoted |
| Fixed Luna | 0/2 | none | Unsuitable for this task under the tested nine-turn policy |

The two fixed-Astra successes each used seven model calls and 24 durable calls.
Their mean reported input was 113,955 tokens, mean model wait 83.297 seconds,
mean proposal-to-feedback total 11.460 seconds, and mean exact-frame count 30.
Two observations do not support a latency distribution, tail estimate or broad
model comparison.

The strongest result is the correctness separation. Fixed Astra reproduced the
task; adaptive did not; fixed Luna reproduced failure. The first block's small
1.850-second fixed-Astra advantage over adaptive is no longer the central result,
because the adaptive route failed the second hard correctness gate.

## Failure-driven interface repair

The v2 driver assumed that a model verification request implied independent
success and asserted before writing a failure result. The engine score and full
finish exchange survived, but the supervisor reported only that the driver had
exited. This is retained as the observed packaging failure.

The v3 candidate classifies three outcomes explicitly:

- successful independent verification → `result.json`;
- bounded turn exhaustion → `failure-evaluation.json` with
  `bounded_turn_limit`;
- visual completion rejected by the evaluator → `failure-evaluation.json` with
  `visual_verify_false_positive`.

The supervisor waits for either persisted outcome and records the negative score
before returning failure. `openttd_finish_outcome_probe_v1.py` replays all three
paths from the second block and passes on Windows and WSL. The v3 path has not yet
run a fresh live episode, so this is a regression-tested repair candidate rather
than live validation.

## Evidence

- Second preregistration and raw runs:
  `results/timing-envelope-openttd-matched-02/`
- Second cross-arm audit:
  `results/timing-envelope-openttd-matched-02/audit.json`
- First block: `OPENTTD_MATCHED_MODELS_V1.md`
- Artifact audit:
  `python research/live_control/audit_openttd_matched_v2.py`
- Outcome regression:
  `python research/live_control/openttd_finish_outcome_probe_v1.py`

The second audit validates 23 model receipts, 84 durable calls and 129 exact
frames on Windows and WSL. Across both blocks the retained evidence contains 47
model calls, 172 durable calls and 270 exact frames.

## Decision

Use fixed Astra for the next fresh OpenTTD episode and validate v3 negative
outcome handling before another route comparison. Then rotate Astra into a
different order position or randomize preregistered block order. Add tasks with
different toolbar state and geometry before treating 2/2 as task-level
reliability. A matched human run remains necessary for human-tempo language.

A subsequent preregistered v3 run validates typed negative finish packaging and
adds a third fixed-Astra success in92.377 seconds. See `OPENTTD_FINISH_V3.md`.
