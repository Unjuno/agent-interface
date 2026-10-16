# Bounded effect wait at a live model boundary

This follow-up combines the partial-terminal model decision with the bounded
verifier wait. It uses two new Chromium sessions and seed 248. The planner sees
strict evidence from `planner_evidence_v4.py`, which recognizes durable journal
revisions v4 through v6 and includes the actual journal revision in each program
record.

The initial integration is retained under `partial-terminal-live-02/`. It stopped
before model delivery because the older presenter correctly rejected the new
`durable-submit-v6` state. No recovery input was sent. Five offline controls then
verify that v4/v5/v6 are accepted while unknown journal revisions and caller
binding conflicts are rejected.

In the corrected live run, the model again chose `submit_once` for the 3/6 prefix
before Return and `wait_and_check` for the 4/6 prefix after Return. Only the first
case admitted one new submission. Each path then used exactly one bounded
`effect_checkpoint` with `wait_ms=6000` and `poll_ms=50`, reached VERIFIED, and
passed the independent saved-value evaluation.

| Quantity | before Return | after Return |
| --- | ---: | ---: |
| Model decision | `submit_once` | `wait_and_check` |
| Model runner | 7.053 s | 5.356 s |
| Input / output / reasoning tokens | 9,823 / 139 / 54 | 9,822 / 82 / 42 |
| New input submissions | 1 | 0 |
| Post-decision effect calls | 1 | 1 |
| Verifier samples | 97 | 1 |
| Expired admission to VERIFIED | 14,139.072 ms | 6,833.855 ms |
| Runtime events / exact frames | 128 / 29 | 98 / 23 |

For the before-Return path, the previous live run needed ten post-decision effect
calls and 17 durable calls in total. The current path needs one and eight. This
reproduces the round-trip reduction with a real model decision in the loop.

The earlier admission-to-VERIFIED time was 15,422.596 ms, versus 14,139.072 ms
here. The model runner also changed from 8.143 to 7.053 seconds, so the difference
does not isolate interface latency. Planner input increased by about 20 tokens
because v4 exposes journal provenance. This remains two authored cases with an
explicit Return-boundary prompt, not a reliability distribution or human-speed
comparison. The long poll still holds the caller journal lock and performs
filesystem sampling rather than receiving an application event.

Artifacts are under `results/partial-terminal-live-02/`,
`planner-evidence-controls-04/` and `partial-terminal-live-03/`.
`audit_partial_terminal_wait_v1.py` checks source hashes, the retained integration
failure, presenter controls, prompt/image/evidence binding, raw model events,
input admissions, one-query completion, effects, exact frames, releases,
independent scoring and cleanup on Windows and Linux.
