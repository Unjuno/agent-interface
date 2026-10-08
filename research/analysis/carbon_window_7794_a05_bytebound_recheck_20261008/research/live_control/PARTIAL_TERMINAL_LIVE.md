# Model decisions across a partial terminal

A completed program is not required for an irreversible application action to
have happened. This experiment makes that boundary visible by expiring the same
six-step Chromium program on opposite sides of its `Return` step.

Both cases use the same seed, exact target value and fetch-based delayed-effect
fixture. The page below the browser chrome is pixel-identical at the decision
point. The only material distinction is the execution prefix retained in strict
planner evidence:

| Case | Expired prefix | Calibration after 5.5 s | Model decision | New input | Final score |
| --- | ---: | --- | --- | ---: | --- |
| before Return | 3/6 | UNKNOWN, false | `submit_once` | 1 | true |
| after Return | 4/6 | VERIFIED, true | `wait_and_check` | 0 | true |

The fourth completed step in the second case is `Return`. Although its following
wait and observation never completed, the server had already received the POST.
The first effect checkpoint was still UNKNOWN. The model read the ordered prior
steps and `steps_completed`, waited without replay, and the first post-model
checkpoint was VERIFIED.

In the first case `Return` is outside the completed prefix. The model issued a
new four-step submission through a fresh clock and admission. That new program
completed. Its delayed effect stayed UNKNOWN for nine 500 ms polls and became
VERIFIED on the tenth. This exposes another current cost: without an event-driven
effect readiness signal, safe completion needed 17 durable calls and 10
post-decision checkpoints.

| Quantity | before Return | after Return |
| --- | ---: | ---: |
| Model runner | 8.143 s | 6.126 s |
| Input / output / reasoning tokens | 9,803 / 123 / 38 | 9,803 / 88 / 52 |
| Expired admission to terminal | 1,320.532 ms | 1,300.782 ms |
| UNKNOWN call end to next action/query | 8,876.950 ms | 6,164.600 ms |
| Expired admission to VERIFIED call end | 15,422.596 ms | 7,602.338 ms |
| Runtime events / exact frames | 145 / 28 | 97 / 22 |

These are two authored cases, not a decision reliability distribution or a human
comparison. Expiry is induced with a bounded wait for a deliberately absent X11
title, so this establishes interruption semantics in the shared runtime rather
than an organic application failure. The prompt explicitly explains the
submission boundary. Cost is unavailable.

The first calibration used pixel quietness as a delay and failed because quietness
was correctly reached in about 310 ms; its program completed and submitted. The
second calibration reached the intended `3/6 expired` state, but the independent
evaluation reply exceeded its three-second query timeout by about 6 ms. Both are
retained under `results/partial-terminal-01/` and `-02/`. The corrected no-model
calibration is `partial-terminal-03/`; the live run is
`partial-terminal-live-01/`.

`audit_partial_terminal_v1.py` verifies source hashes, both retained failures,
the no-model causal calibration, exact prompt/evidence/image binding, raw model
arrivals, completed prefixes, input admission differences, effect logs, saved
bytes, exact frame reconstruction, release and independent success on Windows
and Linux.

The bounded-wait follow-up preserves both model decisions while replacing the
ten-query fresh-submission tail with one verifier query. See
`PARTIAL_TERMINAL_WAIT.md`.
