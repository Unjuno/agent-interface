# Issue #7424 A04 — continuity/tracking Pareto bound

This is a new, separately frozen T0 allocation, not a rerun of A02 or A03. A03 preserved an empirical tradeoff: first-command continuity passed, but the conditioned PI route worsened the preregistered 21-sample IAE in both eligible cases.

A04 asks whether that cost is specific to A03's PI law or unavoidable in the pinned monotone plant once a 25% first-jump reduction is required. The candidate is an oracle upper envelope, not another controller proposal. It takes the greatest actuator-admissible input on the first update that respects the continuity bound, then the greatest rate-limited input toward the reference on every following update. In this positive-error region, the plant is monotone in applied input; no other admissible sequence can have lower IAE than this envelope.

| Case | A03 cold IAE | A04 envelope IAE | IAE change vs exact A03 raw | Cold first jump | Envelope first jump |
|---|---:|---:|---:|---:|---:|
| No disturbance | 6.023788 | 2.693288 | -3.330500 | 0.20 | 0.15 |
| Step disturbance at switch | 5.646698 | 2.294239 | -3.352459 | 0.20 | 0.15 |

The executed envelope meets both gates in both cases. This falsifies A04's preregistered infeasibility hypothesis for the narrow scalar construction; it shows the A03 PI trajectory's tracking tradeoff is not forced by these actuator bounds. It does not prove that a live receiving controller can realize this policy safely.

## H/T/D/C/U

- H: even the best actuator-admissible sequence under the first-jump bound has higher IAE than the pinned A03 cold-start route in both eligible cases. Result: falsified in both cases.
- T: compare that greedy envelope with the pinned A03 cold-start IAE for no-disturbance and step-disturbance-at-switch; use the same first-order plant, 20 updates, output range [0,1], and 0.2/update slew limit.
- D: support scoped infeasibility only if the oracle reduces the first applied-input jump from 0.20 to at most 0.15, yet exceeds the pinned A03 IAE in both cases; independent recurrence and mutation audits must pass. A saturation case is omitted because its cold first jump is zero and cannot meet a percentage-improvement gate.
- C: the result may be specific to this monotone first-order plant, rate limit, reference direction, and finite horizon. A nonlinear plant, disturbance trajectory, alternate metric, or task objective may have a different frontier.
- U: no live transfer, input owner, model, GUI/game, physical actuator, or user task was exercised. This is only an actuator-envelope result for the two frozen scalar cases; it does not close the live-control gate in #59.

Run from this directory: python3 run_a04.py --raw raw.json, then python3 audit_a04.py and python3 -m unittest -v test_audit_a04.py. The candidate invocation is frozen to one run with no retries. Audit and mutation tests consume only saved raw output. The first independent audit failed because it treated A03 README's rounded 5.65 baseline as exact; A03's pinned saved raw records 5.646697966151. That failure is retained. A later exact source-trace cross-check shows both 20-command cold routes and full-precision IAE values match the immutable A03 raw blob exactly; the candidate was not rerun.
