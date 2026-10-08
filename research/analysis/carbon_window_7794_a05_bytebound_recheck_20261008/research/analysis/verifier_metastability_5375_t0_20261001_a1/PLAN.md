# Issue #5375 T0-a1: post-trigger verifier-queue recovery

**Status:** preregistration / frozen execution package. This deterministic model is synthetic and cannot establish that Agent Interface has experienced a metastable failure.

**Final disposition:** `FAIL_METHOD_CAPACITY_CONSERVATION`; hypothesis not evaluated. See `FORMAL_FAILURE.md`. The frozen raw/audit are retained; no rerun occurred.

## H / T / D / C / U

- **H:** At a frozen post-trigger offered load, at least one feedback regime sustains safety-service impairment under the existing breaker policy, while debt shedding plus a reserved recovery unit restores service without action-authorizing admissions.
- **T:** Exhaustive deterministic factorial: four fixed cases × three policies × 24 ticks. The finite verifier outage ends after tick 3; service is restored from tick 4. Cases: underload (arrival 1, feedback 0), fault-only (arrival 2, feedback 0), and feedback regimes (arrival 2, feedback multiplier 1 or 2). Capacity is three integer units/tick. Compare existing-model `breaker`, `debt_shed_reserve`, and `no_retry`. The model's queue feedback is explicit synthetic offered load `external + feedback_multiplier * prior_backlog` after fault removal. Candidate retains every tick as JSONL. Independent auditor reads only raw JSONL and recomputes queue/debt conservation, service bounds, continuity, and authority admissions.
- **D:** `METHOD_PASS` only if all 12 groups have 24 consecutive rows, all conservation/capacity checks pass, controls exhibit no post-trigger feedback-driven impairment, and `authority_admissions=0` always. `HYPOTHESIS_SUPPORTED_MODEL_SCOPED` only if the breaker arm satisfies the preregistered impairment rule (queue >=12 and zero safety service for each of the final 8 ticks after tick 7) in a feedback case and debt-shed/reserve avoids that rule in the same case. `HYPOTHESIS_NOT_SUPPORTED_IN_FROZEN_GRID` if method passes but no feedback case meets the contrast. Otherwise `HOLD` and report the exact gate; no retry after formal freeze.
- **C:** With feedback multiplier 0, finite trigger debt drains under restored capacity; no self-sustaining impairment should occur. With the trigger absent or bounded retries fully discharged, the original breaker is sufficient.
- **U:** The feedback law and thresholds are synthetic and chosen to represent a plausible positive feedback, not estimated from production. Integer deterministic queues omit concurrency, correlated faults, stochastic arrival/service, breaker transition details, cancellation costs, actual policy semantics, and stationarity. Slow monotone drain is not itself metastability. The result supports no production, real-workload, or causal claim.

## Execution limits and provenance

- Allocation: `circuit-metastability-5375-t0-20261001-a1`.
- Frozen main: `73235730af05375fddf3a9d102d30632e7d43af5` (recheck before publication; do not change scientific sources after formal execution).
- Resource: local Python 3.12 CPU, bounded 288-row run. Docker Desktop UI was observed Engine-running, but Docker CLI daemon requests hang; repository Issue #5085 records no Docker use until exact owner release/allocation. No container launch, stop, restart, or existing-container mutation was performed.
- Formal candidate: exactly one execution of frozen `simulate.py`; retain `candidate.jsonl` unmodified.
- Independent audit: one run of frozen `audit.py` against raw only; no candidate imports. Construction checks are pre-freeze only and not formal evidence.
- No network, GPU, GUI, model, live verifier, or action-authority operation is invoked by the experiment.

## Frozen source hashes (SHA-256)

- `simulate.py`: `3651DB886DB3AB8DD6B31F2BE62EDC1C371B6462548E5A9AF822A9D3DA1F2DD4`
- `audit.py`: `7217D9ABE15882B0A776615EDE24A01F83ED790C21EC7E2F1471C601E1E05E37`
