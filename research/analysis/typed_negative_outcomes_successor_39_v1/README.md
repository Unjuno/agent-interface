# Typed negative outcomes successor #4967

This is a deterministic, pre-model contract rung for Issue #39.

The fixture enumerates 2^7 evidence states across budgets 0, 1, and 2 (384 rows). It compares a candidate classifier with an independently arranged oracle and checks:

- stale or missing authority never becomes success;
- only BLOCKED can be retryable;
- retry budget cannot alter hard safety outcomes;
- every result carries authority=false;
- unknown evidence requires a new observation.

This does not test a model, GUI, runtime, network, task correctness, latency, planner boundaries, or production semantics. It does not grant input or semantic authority.
