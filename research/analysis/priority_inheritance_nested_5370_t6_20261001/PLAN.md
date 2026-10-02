# Issue #5370 T6 — transitive inheritance, cancellation, and aging boundary

Status: preregistered host-CPU synthetic discrete-event experiment. It is not a Docker allocation and makes no production-scheduler claim.

## H / T / D / C / U

- **H:** In a fixed nested lock chain, bounded transitive priority inheritance will let a deadline verifier complete without the priority boost persisting after cancellation; adding wait aging that resets after service will bound background wait without permanently starving medium work.
- **T:** Replay four 20-tick rows on one host CPU: (1) no inheritance, (2) inheritance-only, (3) inheritance plus 3-tick wait aging, and (4) inheritance-only with waiter cancellation at tick 2. A owns outer resource R1 and needs two CPU ticks; B owns inner R2, waits for R1, then needs two ticks; H arrives at tick 1, waits for R2, needs one tick, deadline 7; M has priority 2 and 40 units; U has priority 1. Candidate writes one raw JSON; an independent raw-only oracle reads it once. No model, network, GPU, GUI, application, or external input.
- **D:** Scoped PASS only if the no-inheritance verifier misses; inheritance schedules `M,A,A,B,B,H` and completes H at tick 6 with two service ticks each for A/B; cancellation produces `M,A,M` initially, cancels H at tick 2, and gives no later A/B/H service; aging preserves the critical prefix, first serves U at tick 6, keeps U service gaps at most 3 ticks, and still schedules M after U's first service. Exact four-row/tick coverage and zero independent-audit errors are required. Otherwise report scoped FAIL or STOP; no retry.
- **C:** Hand-authored deterministic single-CPU trace, fixed priorities, two nested resources, finite horizon, fixed arrival/deadline/service values. The model simplifies lock acquisition and assumes a complete wait-for chain.
- **U:** This cannot establish real-time distributions, production priority inheritance, incomplete/adversarial wait graphs, authenticated urgency, remote execution, fairness under general workloads, GUI/runtime behavior, task correctness, safety, or human tempo. No Issue #5370 or #59 gate is closed by this result.

## Freeze and execution boundary

- Issue: [#5370](https://github.com/Unjuno/agent-interface/issues/5370); additive successor rung T6, distinct from the existing T0–T5 and waiter-ordering STOP/audit-v2.
- Candidate SHA-256: `b115895a1b0ebe1ea7c8815f4360cbb05658c939947518ae02f314972cabc556` (`scheduler.py`).
- Candidate test SHA-256: `6761a5f2e391314e777917bf380e0beef50df4aa60198348fa591602a92a0a8f` (`test_scheduler.py`).
- Independent oracle SHA-256: `374531c536da5c01d7e02db431d937691025fd827e0767a664e0655794ef61e4` (`audit_raw.py`).
- Oracle mutation-test SHA-256: `39ab6b915228fffeef6b351e13e0e7023e2a66cb81540afa1f6c1b165bdbf81cd` (`test_audit.py`).
- Runtime: CPython 3.12.10, Windows host, UTC timestamps in the run log.
- Docker Desktop lane: **not authorized**. #5085's shared-lane rule is retained; #5074 has no fresh explicit release to this allocation, and idle Docker inventory is not a lease. This host CPU simulation uses no Docker resources and is not mislabeled as a container result.
- Frozen outputs: `results/formal-01/raw.json`; auditor reads that exact file only after the one candidate invocation succeeds. No rerun or replacement.
