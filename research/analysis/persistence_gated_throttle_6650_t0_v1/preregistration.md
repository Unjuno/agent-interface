# Preregistration — Issue #6650 persistence-gated optional-work throttle T0

Allocation `PERSISTENCE-GATED-OPTIONAL-THROTTLE-6650-T0-20261002-01`  
Frozen main base to be recorded in `FREEZE.json` before formal execution  
Additive path `research/analysis/persistence_gated_throttle_6650_t0_v1/`  
Scope: finite synthetic discrete-event method validation. No runtime scheduler, GUI, model, user, or safety claim.

## H / T / D / C / U

**H.** Under an identical exogenous opportunity trace, a per-session optional-producer controller triggered by a persistent above-target oldest-pending age can reduce stale optional deliveries versus fixed-rate generation, with no greater stale deliveries than a queue-length threshold using the same persistence dwell, ramp, and recovery law. It should not throttle brief bursts that drain before the age target, and it must never suppress mandatory work. This may show no useful increment.

**T.** Freeze deterministic traces for transient burst, sustained overload, zero-dequeue blackout, unequal sessions, variable service time, delayed feedback, mandatory flood, semantic invalidation, and unknown optionality/stream identity. Compare fixed-rate, instantaneous queue-length signal, age-persistence signal, and clairvoyant oracle diagnostic. Queue residence is exactly enqueue-to-service-start (completed sojourn); oldest pending age is a separate monotonic clock and may advance without dequeue samples. Candidate and queue-length comparator share target thresholds, persistence dwell, maximum throttle tiers, deterministic progressive sampling, and recovery hysteresis; only the trigger signal differs. Producer suppression changes only generation of eligible optional requests. Preserve every offered ID, suppression receipt, service event, mandatory terminal, source generation, freshness outcome and per-session policy transition. Stale/missing feedback or unknown scope/optionality retains baseline production and emits a typed reason.

**D.** `PASS_METHOD_SCOPED` iff construction tests pass, the raw-only auditor reconstructs all offered IDs and service outcomes, the burst control enters no age-triggered throttle, the blackout case can trigger from pending-age without any completed sojourn sample, sustained-age policy reduces stale optional deliveries versus fixed-rate and is no worse than queue-length on this frozen threshold, every mandatory ID has the exact same terminal service result as baseline, and all corruption controls are rejected. Any hidden/missing coverage gap, cross-session state leakage, stale-as-current result, or mandatory suppression is `FAIL_METHOD`; absent threshold-crossing discrimination is `HOLD_NO_DISCRIMINATION`. A failure of only the preregistered candidate-vs-comparator outcome criterion is recorded as `FAIL_HYPOTHESIS` rather than repaired by changing frozen parameters.

**C.** Synthetic arrivals/service traces may make the trigger relation unusually clean. Fixed pacing or queue length may be equally effective. A local simulator does not capture endogenous planner choices, shared service contention or correctness/value of observations.

**U.** No real queue delay, planner benefit, freshness benefit, task correctness, latency, token saving, or production stability is measured. The oracle schedule is diagnostic only. A method PASS cannot authorize suppression of unique evidence or any mandatory control/check.

## Environment and freeze

WSLc is unavailable on this macOS host and the previously probed shared OrbStack daemon is nonresponsive; no container is started or modified. This deterministic standard-library simulator has no container-specific behavior, so a host-local CPython run is allowed as method-only fallback. Construction tests first; then freeze source, fixtures and tests, confirm formal outputs absent, run candidate once and independent auditor once, zero retries, and preserve all hashes/exits. A preliminary non-formal probe showed fixed=13, queue-length=3 and age-persistence=6 stale optional deliveries on `sustained_overload`; this is adverse expected evidence for H and is not grounds to tune. The formal run will assess reproducibility and the other frozen gates; report the adverse comparison explicitly.
