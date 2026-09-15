# Control Codec / Compact IR — historical research ladder

**Status: retained design/benchmark track; superseded for current C1 contract evidence by `research/runtime_portability_v0/`.**

## First-principles question

If two model outputs cause the same validated computer-control program, how much repeated representation can be removed from the model boundary without reducing correctness?

## Ladder

```text
C0  verbose JSON / structured action list
C1  compact fixed-grammar primitive IR
C2  compact IR + persistent opcode / field dictionary
C3  persistent semantic method refs + parameters
C4  method refs + short workflow refs
C5  method/workflow refs + session-local target aliases
```

Each level must expand to the same validated semantic operations as its paired baseline.

## Hard gate

A candidate is not promoted if correctness, invalid-program rejection, held-input safety, stale-state behavior, or material tail latency worsens beyond a predefined tolerance. Compactness cannot hide uncertainty or remove information required for a correct action choice.

## Accounting

Until exact model/API usage is available, serialized UTF-8 bytes are only a serialization proxy. Definition, repair, invalidation, and relearning costs must be included for persistent dictionaries/methods/workflows.

The newer `research/runtime_portability_v0/` experiment retained a repaired portable C1 contract, exact provider-usage ledger separation, and stronger conformance evidence. Use that track for current C1 semantics; use this directory for the earlier broad C0–C5 research framing and model-free benchmark.

## Minimum future experiments

1. Persistent dictionary lifetime at equal correctness.
2. Semantic-method amortization including definition/invalidation cost.
3. Workflow hierarchy without assuming longer workflows are better.
4. Stale-interface recovery and deoptimization.
5. Exact same-model provider token accounting on paired hidden tasks.

## Integrity rules

- paired hidden task schedules;
- same semantic AST/execution runtime for codec comparisons;
- no dropping hard operations to improve bytes/task;
- failed tasks count against the candidate;
- include all definition/repair/invalidation costs;
- freeze parameters before hidden audit;
- bytes are not tokens.

See `../../docs/control-codec.md` for the reconciled design note.
