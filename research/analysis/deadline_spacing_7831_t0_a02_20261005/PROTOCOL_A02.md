# Issue #7831 — corrected discrete deadline/spacing T0 (A02)

Status: new, additive allocation. The earlier A01 `HOLD_PRE_FREEZE` and its
four candidate/oracle mismatches remain historical and unchanged. A02 changes
the discrete-time boundary contract before any A02 freeze or formal run.

## H / T / D / C / U

**H.** Across a frozen finite sensitivity grid, deadline-constrained minimum
spacing will use fewer optional reassessments than immediate raw triggering on
both noisy oscillation and transient-burst corpora, while incurring no more
boundary violations than raw-triggered or fixed-period sampling on the hazard
corpus. Every hard invalidation bypasses pacing. When spacing and the
response deadline conflict, immediate YIELD releases before the boundary
whenever such a release is physically possible in the model.

**T.** Pure deterministic integer-tick model; no GUI, model, input, user data,
or runtime change. Eight frozen traces: noisy oscillation, transient burst,
sustained approach, hard invalidation, delayed and missing due measurements,
minimum-gap / deadline conflict, and exhausted optional budget. Compare fixed-period,
raw-event, hysteresis-only, and deadline-spaced policies. Sweep 16 combinations
of decline bound `{1,2}`, uncertainty growth `{0,1}`, release latency `{1,2}`,
and minimum spacing `{2,3}`. A separate oracle exhaustively enumerates every
feasible next reassessment tick, reconstructs all policy rows, releases,
misses, suppressed cues, unknown intervals, and hard-bypass latency.

**D.** `PASS_METHOD_SCOPED` only if every candidate row exactly matches the
independent oracle; the candidate uses strictly fewer optional reassessments
than raw triggering on each noisy/transient trace for every sensitivity row;
it has zero boundary violations on each hazard trace and no more misses than
either raw or fixed-period policies; hard-bypass suppression is zero; and each feasible
spacing conflict YIELD releases strictly before the first unsafe tick. Missing
measurements fail closed. Finite-horizon exhaustion is right-censored, not
relabelled as a spacing conflict. Any mismatch is `FAIL`; if event reduction
or the hazard discriminator changes across the grid, `UNCERTAIN_NO_DISCRIMINATION`.

**C.** Fixed-period or hysteresis may obtain comparable event reduction with
a simpler controller; immediate trigger is preferable when cue arrivals are
reliable; conservative uncertainty bounds or explicit YIELD may dominate.

**U.** Authored trajectories and rate bounds may omit semantic target changes,
non-looming hazards, bursty GUI delivery, real capture/release tails, and
endogenous planner delay. No empirical latency, user benefit, GUI/task effect,
safety guarantee, or production cadence follows.

## Corrected tick and horizon contract

Integer ticks are inclusive at observations. The first unsafe tick `D` is the
first tick with `margin[t] - uncertainty[t] <= 0`. A release is on time only
when `release_tick < D`; equality is a boundary miss. Given a current lower
margin `x = margin[t]-uncertainty[t]` and total per-tick decline bound
`R = decline_bound + uncertainty_growth`, the latest safe next observation
tick `s` must satisfy `x - R*(s-t+release_latency) > 0`. The candidate chooses
the greatest feasible `s` no earlier than `t+minimum_spacing`. If no such
`s` exists while the finite horizon still contains the predicted boundary, it
YIELDs immediately. If the horizon ends before the predicted boundary, the
row is `HORIZON_CENSORED`; horizon end alone never creates a spacing conflict.
Hard invalidation is processed before every paced decision and releases at
`hard_event_tick + release_latency`. An absent scheduled measurement yields
immediately and is never interpreted as safe.

This endpoint contract directly replaces A01's ambiguous finite-horizon and
release-at-boundary semantics. A02's source hashes and freeze are separate;
no A01 outcome is rewritten or counted as an A02 run.
