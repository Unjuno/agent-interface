# Issue #6650 — persistence-gated optional-work throttle T0

This is a finite, deterministic, synthetic discrete-event method experiment. It is not a runtime implementation or evidence about users, models, GUI behavior, planner quality, production demand, or safety.

## Reproduction

The candidate compares fixed generation, a queue-length trigger, and an oldest-pending-age persistence trigger on identical exogenous offer traces. It preserves offered IDs and suppression receipts, separately records completed enqueue-to-service-start sojourn and the age of the oldest pending eligible request, checks source generations at service start, and retains mandatory work. `auditor.py` reconstructs accounting from the frozen fixture and raw event rows; it does not use candidate summaries to establish coverage or freshness.

The host is macOS with CPython 3.14.5. WSLc is unavailable and the shared OrbStack daemon probe timed out, so no container was started. This pure standard-library simulator has no container-specific semantics. The result is host-local and method-scoped.

Before formal execution, from repository root:

```sh
python3 -m unittest research.analysis.persistence_gated_throttle_6650_t0_v1.test_construction -v
python3 research/analysis/persistence_gated_throttle_6650_t0_v1/candidate.py research/analysis/persistence_gated_throttle_6650_t0_v1/fixture.json /tmp/6650-raw.json
```

The formal output itself and its independent audit are one-shot operations recorded in `RUN.json` after `FREEZE.json` is written. Formal artifacts are not to be regenerated in place.

## Interpretation boundary

The preregistered candidate criterion includes noninferiority to queue-length on the frozen threshold. If age persistence reduces stale delivery against fixed generation but loses to queue length, the candidate hypothesis fails; thresholds must not be tuned against that result. A blackout transition without completed sojourn samples is a distinct observable capability, not proof of superior overall control. The clairvoyant oracle is diagnostic only.
