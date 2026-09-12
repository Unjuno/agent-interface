# Control Codec / Compact IR

**Status: proposed active research track.**

## First-principles question

If two model outputs cause the same validated computer-control program, how much repeated representation can be removed from the model boundary without reducing correctness?

The purpose of this track is to measure control serialization independently from observation gating, local execution, and model capability.

## Baseline ladder

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

A candidate is not promoted if any of the following worsen beyond the predefined tolerance:

- task correctness;
- hard-case correctness;
- parser / validator acceptance for valid programs;
- invalid-program rejection;
- held-key / held-button state safety;
- p95 / p99 execution tail attributable to codec overhead;
- stale-method recovery behavior.

Compactness is never allowed to hide uncertainty or remove information required for a correct action choice.

## Primary metrics

Until an actual planner API is connected:

- serialized UTF-8 bytes / successful task;
- serialized bytes / semantic operation;
- definition bytes vs invocation bytes;
- uses-to-break-even for methods / workflows;
- parser + dictionary-resolution latency;
- malformed-program rate;
- validator rejection rate;
- expansion size and expansion depth;
- method / workflow cache hit rate;
- invalidation / relearning overhead.

When model-in-loop accounting is available, add:

- exact text output tokens / successful task;
- exact text input tokens attributable to control schema / dictionary;
- exact image tokens separately;
- model boundaries / successful task;
- end-to-end model-visible latency.

**Bytes are not tokens.** The repository must keep these columns and claims separate.

## Minimum experiments

### E1 — primitive serialization

Generate valid Universal Input ISA programs covering:

- key press / down / up;
- chords;
- text;
- absolute / relative pointer movement;
- button down / up;
- click / drag / scroll;
- focus;
- observe / wait-update / assert.

Compare C0 vs C1 at matched semantics.

Report distributions for 4, 8, 16, 32, and 64 operation programs.

### E2 — dictionary lifetime

Compare:

- no persistent dictionary;
- session dictionary;
- application-lifetime dictionary.

Include dictionary setup cost and invalidation cost.

### E3 — semantic method amortization

Use repeated application workflows and measure:

```text
raw universal program
vs
method definition + references
```

Primary result: break-even use count at equal correctness.

### E4 — workflow hierarchy

Compare short method refs with 2-step / 3-step / longer workflow refs.

Do not assume longer workflows are better. Definition cost and reuse frequency must be included.

### E5 — stale interface recovery

Invalidate a previously useful shortcut / route and measure:

- stale invocation rate;
- deoptimization latency;
- fallback correctness;
- relearning cost;
- total serialized cost across the lifecycle.

### E6 — actual tokenizer / API accounting

Once a real model endpoint is available, replay exactly the same hidden task schedule through each codec and record actual token usage returned by the API.

This experiment, not byte count, is the point at which token-efficiency claims become valid.

## Integrity rules

- paired hidden task schedules;
- same semantic AST and execution runtime for codec comparisons;
- dictionary contents unavailable to the evaluator's hidden ground truth;
- no public-seed exploitation;
- no dropping hard operations to improve bytes/task;
- failed tasks count against the candidate;
- include all definition / repair / invalidation cost;
- freeze codec parameters before hidden audit.

## Promotion rule

Prefer Pareto reporting over one scalar score.

Normal promotion requires:

1. correctness passes the hard gate;
2. at least one primary cost improves materially (normally >=10% unless pure dominance);
3. no material p95/p99 regression;
4. result survives a fresh paired replicate.

## Relation to other tracks

- **Observation Gating** removes unnecessary model-visible visual information.
- **Control Codec** removes unnecessary repeated control representation.
- **Guarded Hierarchical Deoptimization** keeps optimized routes from executing after their dependencies become stale.
- **Universal Control** preserves correctness when no optimization is available.

Together they target both directions of the model/computer boundary:

```text
computer -> model : Observation Gating
model -> computer : Control Codec / Compact IR
```
