# MAP01 expiry clock and release diagnosis

This record compares the retained R142 failure with R157's instrumented
positive attempt, then adds a no-input paired-clock probe on the same Windows
host. The question is whether a strict expiry miss is a true late release, a
clock-domain/adjudication problem, or both. The analysis and next experiment
are specified in [PLAN.md](PLAN.md).

## Findings

- R142 passed the exact ammo effect (50→49), eventual same-generation neutral
  readback, two-second neutral horizon and scoped demo check. It failed its
  fixed 20 ms expiry bracket at 41.941 ms. Its public graph correctly remained
  `SAFE_YIELD / delivery_uncertain`.
- R142's Python 3.11.9 lease clock was `GetTickCount64()` (15.625 ms reported
  resolution); the sampler also recorded QPC `perf_counter_ns()`. Those clock
  coordinates differ by tens of milliseconds on this host. The run has no
  `SendInput` entry/return trace, so it cannot assign the observed interval to
  monitor wake, recovery request, OS insertion, or readback.
- R157 used Python 3.14.2/QPC for the deadline and stage trace. It passed the
  unchanged bracket at 12.0785 ms; the first fully post-expiry W-up read was
  10.7525 ms after deadline. The two recorded release `SendInput` entries
  began +9.0401 ms and +9.7214 ms after expiry; they returned +9.6821 ms and
  +11.0081 ms. Same-generation neutral horizon and exact-call ammo effect
  passed. This is one successful run, not a reliability estimate or a cause
  for R142.
- New no-input probe R01 recorded 2,000 paired reads per interpreter. CPython
  3.11.9: monotonic `GetTickCount64`, QPC `perf_counter`, delta min/median/max
  21.5453/21.75755/21.977 ms. CPython 3.14.2: both clocks QPC, delta
  −0.00195/0/0.00055 ms. Probe evidence is in
  [`clock-correlation-r01`](clock-correlation-r01/).

The clock measurement supports a real cross-domain timestamp hazard, but does
not establish that it caused the R142 41.941 ms sample interval. The state
samples themselves were separated by that QPC interval; the missing fact is
where the serialized expiry and actual release-call entry fall on a verified
common clock. Source inspection also found that the shared boundary auditor
uses `monotonic_before_ns >= deadline_ns` for “fully after.” R142's first
post-deadline W-down sample equals the deadline on both monotonic endpoints,
so that row is not proven post-expiry. This weakens its intermediate
post-deadline duration attribution, while preserving the original conservative
41.941 ms gate failure.

## Reproduction and custody

`probe_clocks.py` takes 2,000 same-process samples without opening an app,
backend, input API, authority, or lease. Conditions, paired timestamp CSV,
summary JSON and source are retained here. R142 and R157 source packets remain
unchanged at their original task-local paths; this document does not rewrite
their first outcomes.
