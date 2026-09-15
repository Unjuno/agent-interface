# O3/G1 retained hold-bound source closure v1

## Purpose

This is an offline source/measurement closure pass on immutable base
`bc21199ac1e22ac34decc9fa1a73190e402480ee`. It makes no new model call, GUI
mutation, OS input or formal allocation. It does not change the frozen v38/v39
runtime or its retained artifacts.

The immediate question is narrower than the existing v38/v39 program-envelope
analysis: how much of a model-wait interval can be attributed to **delivered,
program-bound key hold**, rather than merely to an accepted program whose steps
might include motor input?

## Source finding

The retained path has three distinct clocks that must not be collapsed:

1. `keys_held.input_ack_ns` is emitted only after all requested keys for that
   hold have passed X11 `sync()` and is bound to `id` plus `step`.
2. Normal `up` in `input_owner_v10.py` performs X11 KeyRelease plus `sync()` but
   returns no timestamped event. Therefore exact ordinary release time is absent.
3. For a normally completed hold, `session_v4.Backend.execute` creates the hold
   deadline only after the `keys_held` callback returns, releases all held keys in
   `finally`, and only then takes the final per-step snapshot. This yields a
   conservative release interval without pretending that `step_completed` is the
   release time.

The retained event schema has a second provenance limitation: individual
`input_admission` rows are not tagged with program `id`/`step`; the later
`keys_held` row provides the unambiguous all-key chord binding. The new analyzer
therefore reports **all-requested-keys-down occupancy bounds**, not per-key
physical occupancy.

Cancellation is different. Requested duration is no longer a lower bound after
cancel/expiry. For those paths the analyzer reports only non-negative occupancy
plus the earliest retained verified-empty owner release as an upper bound.

## Concrete retained v39 checks

Two ordinary steps from `plan-0-primary-0-1` illustrate the measurement quality:

| step | requested | all-key down ack to conservative release lower | all-key down ack to release upper | release-bound width |
|---|---:|---:|---:|---:|
| 0 | 350 ms | 350.007 ms | 412.641 ms | 62.634 ms |
| 1 | 350 ms | 350.004 ms | 384.429 ms | 34.425 ms |

These are two source checks, not a distribution. They prove that the retained
trace contains materially tighter actuation evidence than the prior whole-program
envelope, but still not exact normal key-up acknowledgement.

The naturally cancelled v39 `plan-3-primary-0-1` step starts its all-key hold at
`55531947530392` ns and reaches the matched verified-empty interruption release at
`55532149408597` ns, an upper bound of 201.878 ms from all-key acknowledgement.
This is a cancellation/release sample, not an ordinary hold-duration estimate.

## Independent usefulness gap

The retained MAP01 score event is terminal. The trace has typed health/ammo and
exact visual observations, but none of those is an independent timestamped
statement that the controlled task made useful progress. In particular, viewport
pixel change is not equivalent to a kill, navigation progress, survival benefit
or MAP01 exit.

Therefore retained v38/v39 can improve **D/F/R** measurement (delivered input,
authority/freshness intersection, reaction/release boundary), but cannot close
**G/H** (hypothesis-bound useful progress and first independent useful outcome).
The next live allocation must expose an independent progress/scorer event with a
runtime timestamp if it wants to claim useful-control continuity.

## H / T / D / C / U

**H — falsifiable diagnostic hypothesis.** The retained event stream contains
program-bound all-key hold starts and enough ordering evidence to interval-bound
normal release more tightly than program lifetime, while lacking both exact
ordinary release acknowledgement and a timestamped independent first-useful-effect
oracle.

**T — minimum check.** Reconstruct v38 and v39 from their retained `report.json`
and `runtime/events.jsonl`; require every normally completed started hold to have
one `keys_held`, one `step_completed`, at least one per-step observation, ordered
release bounds, and hash the source artifacts. Separately count timestamped
independent useful-effect events and terminal score events. Run the synthetic
normal/cancel regression probe before trusting retained output.

**D — decision.** PASS source closure if all completed holds produce ordered bounds
and the analyzer explicitly reports usefulness timing unavailable when only a
terminal score exists. FAIL if any completed hold violates the frozen execution
ordering or if a supposedly independent event is inferred from visual change.
UNCERTAIN for interrupted holds lacking verified-empty evidence.

**C — ways the hypothesis can break.** A later backend may move the final snapshot
before key release; a future event schema may bind and timestamp ordinary release
directly; an independent scorer may already exist under a different retained
schema. The analyzer is versioned specifically so any such change fails or is
reviewed rather than silently changing the meaning.

**U — principal uncertainty.** Normal release lies between a conservative
duration-derived lower bound and the post-release final-snapshot capture upper
bound. The width is scheduler/capture dependent and accumulates if many short
holds are summed. X11 `sync()` and queried empty state establish X-server delivery
and state, not application semantic consumption. Useful-effect timing uncertainty
is unbounded in the retained pair because only terminal independent scoring is
available.

## Decision for the next build

Do not select a recovery policy from the old program envelopes. Run the retained
bound analyzer first. Even if its aggregate uncertainty is acceptable for a
seconds-scale descriptive plot, the next formal matched comparison should add two
small measurement-only features before changing policy semantics:

- timestamped, program/step-bound ordinary key/button release acknowledgement;
- timestamped independent task-progress/useful-effect scoring.

That produces the Product Hunt-worthy trace if the mechanism works: model wait,
finite local authority, actual delivered input, fresh guard state, revocation and
independent progress can all be shown on one synchronized timeline. If it does
not work, the same trace identifies the failure without a hero-run narrative.

Implementation: `analyze_retained_hold_bounds_v1.py`.
Synthetic regression: `probe_retained_hold_bounds_v1.py`.
