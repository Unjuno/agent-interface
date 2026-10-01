# Issue #5851 T0 — causal critical-path elasticity

**Result: `PASS_METHOD_SCOPED` (synthetic deterministic construction only).**

## Question and method

Can a causal DAG plus a paired region-cost intervention prioritize end-to-end optimization better than local time share or the largest observed span? Six frozen DAG fixtures cover a serial bottleneck, long parallel off-path work, near-tied paths, a critical handoff after off-path work, a topology-changing intervention, and incomplete edge/clock evidence. The candidate uses dynamic programming; the independent oracle exhaustively enumerates endpoint-reaching paths. Each region is halved once in the fixed-topology fixtures.

## Results

- Six cases were produced and independently audited with **0 primary mismatches**.
- All **4/4 corruption controls** were rejected (wrong endpoint, altered delta, numeric claim under UNKNOWN, and numeric claim across route change).
- In `parallel_off_path_long_span`, the 700 ms `diagnostic_encode` wins both total-time and largest-span heuristics, yet its paired endpoint improvement is 0 ms. Halving the 300 ms `model` region improves the endpoint by 150 ms.
- In `critical_handoff_after_off_path_work`, the 450 ms `local_encode` span is off-path and yields 0 ms endpoint improvement; the serial `model` and `handoff` each yield 125 ms under the declared halving intervention.
- In the near-tie case, baseline endpoint is 530 ms. Halving `capture` yields 0 ms, while halving `model` yields 10 ms: the alternative path becomes critical.
- A perturbation that changes the declared branch is `NONSTATIONARY_INTERVENTION` with no numeric elasticity. Missing edge/cross-clock evidence is `UNKNOWN` with no numeric estimate.

## Reproducibility and limitations

Allocation `CAUSAL-CRITICAL-PATH-ELASTICITY-5851-T0-20261001-01`; base main `2fbbd0430359a2de11609372e003c3f6ad632a36`. Candidate and audit were each invoked exactly once using Python 3.14.5 on macOS 26.6.2 arm64. No Docker/OrbStack, live app, model/provider, GUI, or task was involved. Raw outputs, frozen sources, and hashes are retained alongside this report.

This result establishes only that the frozen method and audit behave as specified on these hand-authored fixtures. It does not establish real-agent critical paths, actual latency savings, task correctness, MAP01/GUI efficacy, or safety. T1 needs a retained source-bound trace with synchronized causal handoffs, independently grounded endpoints, a safe intervention, and a separate authorized allocation. Do not treat local-span wins as production optimization evidence.
