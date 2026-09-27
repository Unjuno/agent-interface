# MAP01 OS history acquisition v5 — matched acquisition result

## Decision

**HOLD_NO_EXPOSED_ADVANTAGE** with `PASS_AUDIT`.

This allocation compares only history acquisition architecture: synchronous on-demand history versus continuously retained rolling history. The history classifier, MAP01 initial-door task, semantic action program, temporal contract and 500 ms freshness gate are held fixed.

## First complete result

- on-demand: 8/8 condition success, 8/8 semantic correct, 8/8 transit, stale 0, release failures 0; median age 213.203 ms.
- rolling: 8/8 condition success, 8/8 semantic correct, 8/8 transit, stale 0, release failures 0; median age 250.867 ms.
- paired median `(on-demand age - rolling age)`: -38.677 ms. Positive would favor rolling; the observed value is negative.

The preregistered PASS rule required rolling to be no worse on semantics/transit with zero stale/release failures, plus either at least one on-demand stale yield or >=50 ms paired-median rolling freshness advantage. The hard gates passed, but neither advantage criterion was exposed. Therefore this result is HOLD, not evidence that rolling acquisition is faster/fresher in general.

## Interpretation

V4 established that a freshness-first rolling history can preserve the useful action-effect signal without stale evidence on this fixture. V5 shows that synchronous on-demand history can also satisfy the same 500 ms gate in a fresh matched block. The earlier retained 882.6 ms on-demand stale event therefore appears conditional rather than inevitable.

Architecturally, rolling retention remains useful as an availability mechanism, but this allocation does not justify promoting it on a causal freshness-performance claim. A higher-information successor should vary planner/model wait or capture contention while keeping the acquisition methods fixed, so evidence availability is tested under the latency regime where the original stale failure occurred.

## Audit boundary

The independent audit re-decodes all 32 PNGs, verifies RGB hashes, recomputes history predictions from the frozen calibration, checks 50–100 ms pair gaps, recomputes the freshest eligible rolling pair, verifies the 500 ms age gate and all setup/controller release records, and recomputes the preregistered decision.

No model calls, automap, pause/save-state, controller-visible position/angle, or direct game action vectors are used. This is not a MAP01-clear, long-horizon navigation, general GUI or speedup result.
