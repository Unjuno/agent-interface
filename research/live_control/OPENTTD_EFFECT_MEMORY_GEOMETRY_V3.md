# OpenTTD bounded effect memory on changed L geometry

## Frozen allocation

The seed991004 fixture changes the byte-pinned save, map origin, target and guard
tiles, and visible screen position while keeping the five-tile L semantics. Its
target is684,685,686,750,814, compared with977,978,979,1043,1107 in the
seed991003 fixture. The geometry-derived scorer, exact49-tile guard, initial
negative score, save stability and two observer-only restores pass on Windows
and WSL before model execution. All fixture processes release.

V11 was then preregistered as the first and only changed-geometry allocation.
It retains the v9/v10 all-Astra-medium route, twelve-turn bound, task wording,
tree-transparency pre-action, checkpoint grammar, one-unresolved-drag effect
memory and independent scorer. There was no retry or manual intervention.

## Result: task complete, completion not recognized

The model opens and identifies the road controls, then makes two distinct
drags. Turn5 builds target tiles684..686. The effect remains `uncertain` through
five inspection-only turns and becomes `observed` on turn11. Turn11 then builds
tiles750 and814. Turn12 still calls that second effect `uncertain`, so the model
does not request verification before the bound.

The turn-limit finish obtains an independent engine score. All five target
tiles are owned roads, all four ordered connections are bidirectional, all four
forbidden tiles remain clear and the surrounding guard is unchanged. Observer
transitions94 and236 change only684..686 and750/814, followed by16 stable
complete records. All25 terminals verify released keys and buttons. Neither
completed segment is dragged twice.

This is independent task success at the turn limit. It is not controller-verified
hard success because the model never declared semantic completion. The timing
recorder therefore has no `semantic_completion_detected` endpoint.

| Endpoint | V11 changed geometry |
| --- | ---: |
| independent task score | success |
| controller-verified hard success | false |
| model turns | 12 |
| input tokens | 204,114 |
| cached input tokens | 104,448 |
| output tokens | 2,751 |
| model wait | 195.604s |
| proposal-to-feedback | 27.467s |
| initial observation to feedback after the second drag | 211.632s |
| semantic completion detected | not recorded |
| durable calls | 50 |
| exact frames | 62 |
| verified release terminals | 25 |
| repeated completed-segment drags | 0 |

The motor result transfers to this one changed geometry, but effect resolution
does not transfer efficiently. Compared with v9/v10, the first effect needs five
inspection turns instead of one, and the second remains unresolved at the bound.
No speed, token, population, human-tempo or general geometry claim follows.

## Two retained packaging defects

The v2 finish classifier correctly writes `result.json` with
`bounded_turn_limit_with_independent_task_success`. The supervisor still waits
only for `failure-evaluation.json` on its limit path, sees the already exited
driver and raises. The raw successful score and exit0 are intact, but the
supervisor timing result is absent. The runtime manifest also inherits stale
seed991003 scope text from its imported v1 protocol even though its save hash,
preregistration, driver plan and evaluator contract identify seed991004.

The v11 setup also initially reused the tracked `pointer_socket_entry_v9.py`
filename. After execution, that pre-existing file was restored byte-for-byte
from HEAD. The exact executed source is retained under its preregistered SHA in
`frozen_sources/`, and the audit resolves and verifies that archive. Future
changed-geometry work uses a new entrypoint filename.

`persisted_outcome_v1.py` removes the filename assumption by selecting exactly
one typed result or failure and checking its finish kind. Archived v9 visual
success, v11 bounded-limit success and v8 independent failure select correctly;
five missing, contradictory, mismatched and mislabeled controls refuse on
Windows and WSL. Integrate that selector and correct fixture provenance before
another live geometry allocation.

## Decision

Hold bounded effect memory. The changed geometry demonstrates correct actuation
without repeated completed-segment input, while exposing excessive inspection
and missing semantic completion. Repair finish packaging and provide a local,
task-independent completion/effect signal that can end the second checkpoint
without another full model judgment. Do not repeat v11.

The first pixel-only receipt follow-up is now rejected. Although an archived
threshold separates nine selected new effects from two repeated completed-segment
drags, a preregistered A/B/B/A fixed-context comparison reverses the desired
planner result: raw baseline is `observed`2/2 while receipt is `uncertain`2/2,
at+156 input tokens/call. The receipt mixes evidence with a no-action-authority
statement and makes Astra more conservative. Do not run it live. Next separate
an agent-authored local postcondition from action admission and evaluate it as an
in-program barrier. See `PERSISTENT_EFFECT_RECEIPT_V1.md`.

Primary evidence:

- `results/timing-envelope-openttd-l-11/preregistration.json`
- `results/timing-envelope-openttd-l-11/audit.json`
- `../openttd_task/results/l-geometry-02/audit.json`
- `results/persisted-outcome-v1-probe.json`
