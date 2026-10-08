# Issue #6657 T0 — notification-conditioned sampling reactivity

## Lineage and scope

This is a method-only finite replay for open Issue #6657. It does not use
participants, a live GUI, notifications to a real person, a model, or user data.
It preserves the distinction in #6200 between clock-time sampling and
episode/check-in sampling; the new factor is whether a notification changes the
modeled inspection schedule. It is not #6067's visual capture-phase test.

## H / T / D / C / U

**H — issue-level hypothesis.** In an eligible asynchronous task family,
randomized progress-notification exposure may change voluntary human
check/takeover timing relative to silence, and notification-conditioned
check-ins may estimate time-weighted no-useful-progress exposure differently
from independent clock-time epochs. Direction is unknown. This T0 does not test
human behavior or the causal hypothesis; it validates whether the estimands and
their separation are computable on a known trace.

**T — finite method experiment.** Freeze a 60-tick asynchronous trace with
useful-progress events at ticks 0, 4, 30, 33, and 60, a two-tick stale threshold,
and long/short gaps. Evaluate silence, milestone, and noisy-status notification
arms using one frozen base check schedule and one-tick notification reaction
latency. Also include a visible-notification/no-reactivity control. Compute
(1) exact clock-time no-progress exposure over all ticks, (2) a seeded
with-replacement exogenous epoch sample plus its exact uniform-epoch expectation,
and (3) the no-progress fraction among check-ins. Candidate emits every tick,
gap, notification, check and denominator. A separately implemented auditor
reconstructs from the fixture, compares every canonical field, and rejects
controls that leak epoch draws into check scheduling or omit the longest gap.
Construction tests are separate from the one-shot candidate and auditor CLI
invocations. Host CPU only; no container is started because OrbStack currently
has other active research machines and this finite standard-library method has
no container-specific semantics.

**D — method-only decision.** `PASS_METHOD_SCOPED` iff the exact tick-weighted
truth and exact uniform random-epoch expectation agree; candidate and independent
auditor agree on all denominators and arm schedules; notification-reactive arms
produce their frozen, distinct check schedules; the no-reactivity control equals
silence; the long-gap episodes remain in all denominators; and both corruption
controls are rejected. Any missing tick/gap or mismatch is `FAIL_METHOD`; missing
or ambiguous time/progress provenance is `HOLD`. No outcome of this T0 is a
human-reaction or notification-effect result.

**C — competing explanation.** Exogenous clock-time epochs may already answer
the only relevant exposure question; notification-conditioned checks may merely
sample progress milestones or stale periods by construction. In a real study,
task phase, notification visibility, check latency, and voluntary checking may
explain observed differences. Random-epoch and notification-conditioned frames
must therefore remain separate.

**U — unknowns and limits.** Scripted notification schedules do not model human
attention, voluntary takeover, comprehension, trust, interruption cost, or
notification-caused behavior. One finite trace does not estimate a human
population effect or validate a useful-progress oracle. The T0 cannot determine
whether notifications help or harm users, nor support changing product policy.

## Frozen schedule semantics

- Time domain: integer ticks `0..59`; intervals are half-open.
- Useful-progress receipt at tick `t` resets age before scoring tick `t`.
- Tick `t` is no-useful-progress iff `t - latest_useful_tick > 2`.
- Clock-time truth is the number of no-progress ticks divided by 60.
- The exogenous epoch sample uses Python `random.Random(seed).randrange(60)` with
  replacement. The exact expectation is independently enumerated over all 60
  possible single-tick epochs; the realized finite sample is reported separately.
- Base check ticks: `[8, 20, 31, 45, 57]`.
- A reactive check occurs one tick after each notification; coincident checks
  are deduplicated and the raw record retains both causes.
- The no-reactivity control exposes the milestone notifications but does not
  add notification-triggered checks.
- All ticks, including long no-progress gaps and the final horizon tail, remain
  in the clock-time denominator.

## Provenance

The selected issue, `main` HEAD, source files, and fixture are recorded in
`FREEZE.json` before the single formal candidate execution. The candidate writes
`results/t0-01/raw.json` once; the independent auditor reads it and writes
`results/t0-01/audit.json` once. No retry or replacement is permitted.
