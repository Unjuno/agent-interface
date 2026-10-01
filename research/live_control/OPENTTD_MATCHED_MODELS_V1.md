# OpenTTD matched model-route study

Status: preregistered descriptive evidence; no route promotion.

Three fresh OpenTTD episodes used the same canonical save, task, initial app
geometry, source revision, proposal schema, prompt policy, nine-turn bound and
independent engine evaluator. The declared experimental variable was the model
route: Luna-low for every turn, Astra-medium for every turn, or two Luna-low
turns followed by Astra-medium. Execution order was fixed before the first arm,
and a failing arm was retained without retry.

## Result

| Arm | Hard result | Model turns | Initial observation to semantic completion | Model wait | Proposal to useful feedback | Reported input tokens | Exact frames | Durable calls |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fixed Luna-low | FAIL | 9 | unavailable; no semantic completion | 103.262 s | 29.599 s | 126,626 | 65 | 36 |
| Fixed Astra-medium | PASS | 7 | 98.351 s ±50 ms | 84.118 s | 12.582 s | 114,186 | 32 | 24 |
| Adaptive, 2 Luna then Astra | PASS | 8 | 100.201 s ±50 ms | 79.800 s | 18.576 s | 126,424 | 44 | 28 |

The fixed-Luna episode exhausted all nine turns. Independent evaluation found
the requested target road and bidirectional connections absent, the forbidden
row clear, and the surrounding-road guard violated on tiles 613, 614 and 615.
This is a task failure rather than a wrapper failure.

Both Astra-containing episodes passed target ownership, bidirectional
connectivity, forbidden-row and unchanged-surroundings checks. In this one
matched block, fixed Astra completed 1.850 seconds sooner than adaptive, used one
fewer model turn, 12,238 fewer reported input tokens, 12 fewer exact frames and
four fewer durable calls. Adaptive had 4.318 seconds less wrapper-observed model
wait, but spent 5.994 seconds more from proposal publication to useful feedback.
Those differences are observed episode values, not estimates of expected model
performance.

## What the comparison changes

The earlier adaptive v7 and v8 task successes showed that escalation could
finish this task after Luna exploration. They did not show that escalation was
better than using Astra from the beginning. The matched block removes that
particular missing control. Its result does not support promoting the fixed
two-turn adaptive route for this task. Fixed Astra is the current replication
candidate because it was the only arm to combine hard success with fewer turns,
tokens, frames and durable calls in this block.

This does not establish that fixed Astra is generally better. The study has one
fixed-order episode per arm, model outputs are stochastic, OpenTTD advances
during visual interaction, and no human allocation was collected. Repeated
counterbalanced blocks and a matched human baseline are required before a route
or speed claim. Provider receipt, provider first token, runtime receipt and exact
OS injection endpoints remain explicitly `NOT_RECORDED`.

A later reversed-endpoint block changes the cumulative hard results to fixed
Astra 2/2, adaptive 1/2 and fixed Luna 0/2. The cumulative analysis supersedes
the single-block route comparison here; see `OPENTTD_MATCHED_MODELS_V2.md`.

## Evidence and audit

- Preregistration: `results/timing-envelope-openttd-matched-01/preregistration.json`
- Cross-arm audit: `results/timing-envelope-openttd-matched-01/audit.json`
- Raw arms and controls: `results/timing-envelope-openttd-matched-01/`
- Audit command: `python research/live_control/audit_openttd_matched_v1.py`

The audit checks preregistered and per-arm source hashes, replays every durable
exchange against the runtime event stream, validates every model event and
reported usage receipt, decodes 141 exact frame packets, verifies released input
state, recomputes all same-clock intervals, and checks the independent score. It
passes on Windows and WSL.

## Decision

Do not promote the authored adaptive route. Retain it as a tested fallback and
retain the fixed-Luna failure. Use fixed Astra as the next OpenTTD replication
arm, then counterbalance execution order and collect a human run under the same
task allocation. Separately, reduce the 0.8-second tooltip dwell only with a
matched correctness-preserving comparison; model waiting remains the dominant
measured cost in both successful arms.
