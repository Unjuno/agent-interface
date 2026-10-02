# Issue #6657 T0 result — estimator separation on a scripted trace

Disposition: **`PASS_METHOD_SCOPED`**. The one frozen candidate exited 0; the
separately implemented interval-based auditor exited 0 with all eight gates
true. Candidate/auditor invocations: 1/1; retries/replacements: 0/0. Raw and
audit SHA-256 values are recorded in `RUN_RECORD.json` and `SHA256SUMS`.

## H / T / D / C / U

The full frozen H/T/D/C/U is in `PLAN.md`. In brief, the T0 asks whether three
distinct quantities can be recovered on the same known async trace: exact
clock-time exposure, an exogenous random-epoch sample/expectation, and
notification-conditioned check-in exposure. It tests method accounting only;
the issue-level human/notification hypothesis remains untested.

## Frozen finite result

The 60-tick trace has useful-progress gaps of 4, 26, 3, and 27 ticks. Under the
frozen rule (`age > 2` ticks), **48/60 ticks (0.80)** are no-useful-progress
ticks. The exact expectation over a uniformly selected clock epoch is also
0.80. The separate seeded sample selected 10/12 no-progress epochs (0.8333),
which is retained as one finite sample and not substituted for the exact
population expectation.

| Scripted inspection arm | Check-ins | No-progress check-ins | Check-in fraction |
|---|---:|---:|---:|
| Silent baseline | 5 | 4 | 0.8000 |
| Milestone notification, reactive | 7 | 4 | 0.5714 |
| Noisy status, reactive | 11 | 10 | 0.9091 |
| Milestone visible, nonreactive control | 5 | 4 | 0.8000 |

The independent auditor reconstructed all candidate fields and all 60 clock
ticks using progress intervals, not candidate code. All 8 gates passed,
including exact uniform-epoch expectation, schedule differences in the
reactive arms, equality of the nonreactive control and silence, and rejection
of two mutations: random-epoch schedule leakage and omission of the longest
progress gap.

## Interpretation / limits

This demonstrates that a check-in-conditioned estimate can differ from the
clock-time frame when the check schedule is scripted to react to notifications;
the direction differs by the scripted notification schedule. It does **not**
show that actual people check or take over in these ways, that notifications
caused any human behavior, or that an interface notification policy is useful
or safe. The full #6657 hypothesis requires a separately consented and
ethically reviewed human study with independent clock-time sampling. No T1 is
authorized or claimed here.

Execution was native macOS host CPU only (Darwin 25.6.0 arm64, CPython 3.14.5).
OrbStack was not used because its read-only machine list showed active machines
for other research; this finite standard-library method has no
container-specific semantics. No GUI, model, participant, user data, network,
or external effect occurred.
