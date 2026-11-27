# Freshness-gated hedging for read-only GUI observations

- **Source:** Closed [Issue #7383](https://github.com/Unjuno/agent-interface/issues/7383); separate merged synthetic allocations in [PR #7400](https://github.com/Unjuno/agent-interface/pull/7400) (WSLc) and [PR #7415](https://github.com/Unjuno/agent-interface/pull/7415) (host CPU).
- **Status:** Two finite simulator allocations passed scoped method/hypothesis gates. No real GUI capture route, current critical path, application effect, or adoption was tested.
- **Prior art:** Dean and Barroso's [tail-at-scale hedged requests](https://doi.org/10.1145/2408776.2408794) and Shah et al.'s [redundant-request latency/load analysis](https://doi.org/10.1109/ALLERTON.2013.6736597) motivate the tradeoff. They do not establish benefit on mutable GUI surfaces.

## Idea

For one strictly read-only observation request, delay one duplicate until a threshold learned from separate calibration traces. Admit only the first complete response that remains bound to the correct request, source generation, target and currentness gate. Retire the losing request where possible and count its work. If identity/currentness is uncertain or responses disagree, return UNKNOWN/YIELD; never combine two raced captures into an apparently atomic snapshot or let the earliest bytes bypass action-admission checks.

This mechanism is useful only if complete-current observation acquisition is an evidenced straggler on the selected route's critical path. Correlated service times, shared compositors/queues, cancellation lag and generation changes can remove the gain or make duplication harmful.

## Separate results

**WSLc allocation** `OBSERVATION-HEDGE-7383-T0-WSLC-20261004-01` used 40 cases in each of five strata and three arms (600 arm rows), with an 11 ms threshold. Candidate and independent auditor each ran once; the auditor reconstructed all 600 rows, found no errors and rejected 4/4 corruptions. In the authored heavy-tail stratum, p95 fell from 80 ms to 14 ms and mean-work ratio was 0.541. Correlated delays gave no p95 gain and 12.8% more work; a shared queue worsened p95 from 12 ms to 20 ms; cancellation lag lowered p95 from 30 ms to 18 ms but increased work 18.1%; generation-flip p95 remained unavailable because only 5/40 delayed responses were admissible. Requested cgroup/swap limits were not independently verified. The raw candidate was recovered from the committed base64/gzip transport and its 168,136-byte SHA-256 matches `RUN.md`.

**Host CPU allocation** `GUI-OBSERVATION-HEDGING-7383-T0-20261004-A01` used a disjoint calibration deck and 1,000 matched evaluation rows across five conditions. The independent auditor reconstructed all rows and rejected 4/4 corruptions. In the independent heavy-tail fixture, p95 fell from 89 ms to 12 ms, delayed-secondary service was 4.46% of primary work, and deadline misses fell from 20 to 0. Perfectly correlated and serialized shared-server controls showed no p95 gain. In the generation-transition condition, stale responses were refused. This ran on host CPython after OrbStack's missing-blob error prevented container use.

These are distinct freezes with different thresholds, inputs and execution environments. Do not pool them as one replication or transfer either result to real capture latency. Both establish only behavior of their deterministic synthetic simulators. Exact host artifacts and tests are in the [host package](../../research/analysis/observation_hedging_7383_t0_20261004/REPORT.md); the WSLc result and recovered raw are recorded in its [run record](../../research/analysis/observation_hedge_7383_t0_wslc_a01/RUN.md).

## Adoption boundary

Before a new allocation, establish that a real eligible read-only capture is on the critical path and characterize source-generation changes, service-time dependence, shared queues, cancellation and application-owned effects. Only then consider a separately authorized private disposable Xvfb test with two read-only workers and an independent effect oracle. No model, user desktop, consequential action, network or GPU is needed for that bounded follow-up. These synthetic passes alone do not justify deployment or a runtime change.
