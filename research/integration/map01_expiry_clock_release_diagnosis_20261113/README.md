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
used `monotonic_before_ns >= deadline_ns` for “fully after.” R142's first
post-deadline W-down sample equals the deadline on both monotonic endpoints,
so that row is not proven post-expiry. The shared auditor now requires strict
`>` and has an equality regression. Applying it read-only to retained R142
excluded seven equality rows; the first strictly post-deadline sample still
saw W down, but the attributed post-deadline down duration changed from
39.9998 ms to 24 ms. The strict audit remains `not_verified`, with the same
41.941 ms QPC gap and 42.1552 ms outer bracket. The original packet and audit
remain unchanged. See [corrected derivation](R142_CORRECTED_ADJUDICATION.json).

The 59-test `map01_numeric_ammo_oracle_20261111` suite passes in CPython 3.11.9
normal and optimized (`-O`) modes after the fix. This verifies the offline
adjudicator contract; the separate R158 section records the live QPC-native
release qualification and its limits.

## Fresh integrated replication R158

R158 then exercised one fresh public compiled-supervised Win32 MAP01 attempt
from source `3170337504f69051c79e3279352b7dee4504e7ac`, with the runtime tree
matching `origin/main` at freeze. Its QPC clock preflight qualified before
dispatch. All 19 runtime gates passed without retry, replay, or relaxing the
10 s graph budget / 20 ms boundary. The conservative expiry bracket was
10.4057 ms; first W-up was read 8.3652 ms after expiry. Two traced native
`SendInput` calls began +7.3236/+7.9675 ms after expiry. The exact public call
produced an independently verified ammo transition 50→49, recovery confirmed
same-generation all-up, and the two-second neutral horizon passed over 183
samples (maximum gap 11.5357 ms). Same-run demo analysis found no recorded
forward command after expiry/release through the scoped horizon. The owned
process exited normally without forced termination.

This is a scoped positive replication, not reliability, MAP01 completion,
proof against every queued Windows message, or an efficiency comparison. The
packet's preregistration `Attempt` string differs from the frozen conditions
ID; that clerical mismatch is preserved in the result summary and was not
corrected after the attempt. The local R158 packet is
`private-packets/map01_native_windows_deep_trace_20261113_r158`; its post-exit
manifest verified 81/81 files and its final additive manifest verified 87/87.
See `R158_RESULT_SUMMARY.md` in that packet.

## Reproduction and custody

`probe_clocks.py` takes 2,000 same-process samples without opening an app,
backend, input API, authority, or lease. Conditions, paired timestamp CSV,
summary JSON and source are retained here. R142 and R157 source packets remain
unchanged at their original task-local paths; this document does not rewrite
their first outcomes.
