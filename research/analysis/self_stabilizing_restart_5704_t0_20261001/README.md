# Authority-safe restart convergence — Issue #5704 T0

Finite model experiment for the restart/convergence idea in [Issue #5704](https://github.com/Unjuno/agent-interface/issues/5704). This does not change runtime behavior. See [preregistration](PREREGISTRATION.md), [local construction checks](LOCAL_CI.md), and [results](RESULTS.md).

`model.py` enumerates the candidate protocol; `audit.py` independently enumerates the frozen state space and fair schedules from candidate JSONL without importing candidate code. Raw construction and formal artifacts are kept in separate subdirectories. Scope is only the explicitly encoded finite model and trust/fairness assumptions.
