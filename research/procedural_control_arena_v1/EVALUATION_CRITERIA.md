# Arena v1 evaluation criteria

These criteria were frozen in Issue #4695 **before** auditing or repairing the Arena v1 presentation. They define what the benchmark instrument should be evaluated against; they are not agent-performance results.

## Research basis

The criteria synthesize several benchmark-design lessons rather than copying one benchmark:

- [OSWorld](https://arxiv.org/abs/2404.07972): executable computer environments, realistic rendered observations, reproducible setup, and execution-based evaluation.
- [OSWorld 2.0](https://arxiv.org/abs/2606.29537): long-horizon/dynamic computer use, visual-spatial precision, implicit state and information arriving during execution.
- [BrowserGym](https://arxiv.org/abs/2412.05467): explicit standardized observation/action spaces and reproducible evaluation infrastructure.
- [Procgen](https://arxiv.org/abs/1912.01588): fast procedural environments and held-out generated levels for measuring generalization rather than memorization.
- [The Benchmarking Epistemology](https://arxiv.org/abs/2510.23191) and [Measuring what Matters](https://arxiv.org/abs/2511.04703): benchmark scores support capability claims only when the operationalization has adequate construct validity.
- [Accounting for Variance in Machine Learning Benchmarks](https://arxiv.org/abs/2103.03098): randomize relevant variation and account for repeated-test variance before concluding that one procedure improves over another.

The Arena remains a synthetic screening instrument. None of these references imply that passing Arena establishes real-world computer-use capability.

## Frozen criteria

### E1 — Construct validity / policy leakage

The visible task must require the intended capability. Goal and constraint information may be visible. Step-by-step control-policy coaching, mechanic names, hidden-stage labels, or direct procedural hints that make the intended capability unnecessary must not be the default evaluated presentation.

### E2 — Observation/action fidelity

The evaluated controller should act from ordinary rendered evidence through ordinary keyboard, pointer and text input. Seed, object IDs, future stage graph, scorer state, generator state and privileged action APIs must not be controller-visible.

### E3 — Outcome validity / independent effects

Success is defined from world effects plus forbidden/collateral effects, not from reproducing one exact action trace. Multiple valid physical trajectories should remain admissible when the task semantics permit them.

### E4 — Anti-shortcut / generalization pressure

Fresh seeds are necessary but insufficient. Presentation, semantic mapping, order/composition and eventually generator families should vary. Development-known and held-out evaluation distributions must be distinguishable.

### E5 — Difficulty identifiability

Causal difficulty axes must be independently sweepable. A claimed frontier should not silently move unrelated axes. Coupled effects belong in explicitly declared interaction studies.

### E6 — Temporal validity

Realtime claims require the world to continue while the rich model is waiting. Simulation time and wall time remain separate. Fixed-step execution supports deterministic mechanics/replay, not wall-time performance claims.

### E7 — Failure attribution

Evaluator diagnostics should distinguish, where observable, wrong selection/grounding, controller decision or inhibition, stale state, motor precision, typing/focus, realtime deadline, recovery, and infrastructure/evaluator failure. Oracle diagnostics remain evaluator-only.

### E8 — Reproducibility and statistical reliability

Exact episodes must be replayable after evaluation, while formal episodes are fresh before execution. Paired arms use equivalent episode schedules, isolated sessions, counterbalanced order, repeated seeds, and uncertainty/variance reporting.

### E9 — Efficiency under correctness

Correctness is a hard gate. Conditional on correctness, measure wall/model wait, model boundaries, observations/images, token/cache accounting where available, CPU/RAM and recovery/fallback cost. Speed purchased by correctness loss or uncontrolled resource growth is not an improvement.

### E10 — Ecological / transfer validity

Synthetic primitives should correspond to actual computer-control demands, but Arena results remain screening evidence. Retained mechanisms require independent transfer checks on real applications or other domains.

### E11 — Instrument quality

The benchmark itself should remain cheap, resettable, inspectable by the evaluator, deterministic where declared, and low enough overhead that rendering/scheduling does not dominate the phenomenon being measured.

### E12 — Task specification separation

Separate **what outcome is desired** from **how to physically perform it**. Natural-language task goals may be a deliberate axis, but procedural coaching must be independently switchable rather than embedded in every primitive. Semantic task understanding and low-level control should be measurable separately and in composition.

## Evaluation order

For changes to this benchmark:

1. freeze the relevant evaluation criteria and claim boundary;
2. audit the current instrument without changing it;
3. retain the audit, including failures;
4. repair only observed deficiencies;
5. rerun the same criteria/tests;
6. keep unresolved criteria visible rather than converting a construction PASS into a benchmark promotion claim.
