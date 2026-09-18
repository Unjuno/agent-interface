# Control Codec and Compact IR

> **Document role:** research/design note for compact model-boundary representation. It does not define the current stable runtime protocol. Current promoted runtime semantics live under [`../runtime/`](../runtime/) and evidence status is indexed in [`../RESEARCH.md`](../RESEARCH.md).

## Why this exists

Agent Interface already measures `planner bytes`, but measurement alone does not define how model-visible control should be encoded.

A capable planner should not need to repeatedly emit verbose JSON, repeat stable field names, or restate an execution sequence that the runtime already knows. The interface should preserve the same control semantics while minimizing repeated serialization across the model boundary.

This document separates three concerns that are easy to conflate:

1. **semantic control** — what operation should happen;
2. **runtime representation** — the validated AST / executable program used locally;
3. **model-boundary codec** — how that semantic program is serialized for a planner.

The runtime representation should optimize for correctness and validation. The model-boundary codec may optimize for compactness, but must not weaken semantics or safety.

## Core principle

> Compress repeated representation, not required information.

A shorter command is useful only if the runtime reconstructs the same validated operation and the planner still receives the observations needed to choose correctly.

## Candidate ladder

```text
C0  verbose structured actions / JSON-like baseline
C1  compact textual IR with fixed grammar
C2  persistent opcode / field dictionary
C3  persistent app-method references with parameters
C4  short workflow references composed from methods
C5  session-local aliases for repeatedly referenced targets/state
```

The ladder is intentionally incremental. A candidate is promoted only if it preserves correctness and has lower total cost after setup / definition overhead is included.

## Example

A verbose representation might repeat schema structure for every operation:

```json
[
  {"type":"keypress","keys":["G"]},
  {"type":"keypress","keys":["X"]},
  {"type":"type","text":"0.3"},
  {"type":"keypress","keys":["ENTER"]}
]
```

A compact model-boundary form could be:

```text
K:G;K:X;T:.3;K:ENTER
```

After a stable application method is defined, the planner may emit only:

```text
MOVE_X(.3)
```

The runtime still expands the reference into the same validated Universal Input ISA. Compact syntax is not allowed to bypass guards, key/button state validation, retry, state-version checks, or postcondition verification.

## Persistent dictionary vs per-request abbreviations

The main expected gain is not one-character opcodes by themselves. The larger gain comes from **persistent shared structure**:

- stable opcode meanings do not need to be explained every turn;
- an application method is defined once and referenced many times;
- a workflow is defined once and reused;
- common targets may receive session-local references;
- unchanged fields are not repeated.

This makes the problem closer to dictionary compression / bytecode design than to merely shortening English prompts.

## Amortization

Every persistent definition has a cost.

A method or workflow should not be promoted merely because its invocation is shorter. Its total lifecycle cost includes:

```text
definition cost
+ validation cost
+ invalidation / relearning cost
+ all subsequent references
```

The relevant question is therefore:

> After how many successful uses does the compact representation beat the universal baseline at equal correctness?

A local encoding that is shorter in isolation may still be globally worse if it prevents higher-level workflow reuse. Measure the hierarchy as a whole.

## Token accounting

Until a real model/API is connected:

- UTF-8 bytes are a **serialization proxy**;
- character count is a **text-length proxy**;
- observed pixels / image bytes are **visual transport proxies**;
- none of these may be renamed as model tokens.

When model-in-loop measurement is available, record separately:

- text input tokens / successful task;
- text output tokens / successful task;
- image tokens / successful task;
- model boundaries / task;
- tool / interface calls / task.

The codec should be evaluated with the exact tokenizer / API accounting used by the tested planner.

## Safety and correctness constraints

A compact codec must preserve:

- unambiguous parsing;
- explicit held-key / held-button state;
- argument bounds;
- macro expansion limits;
- state-version guards;
- uncertainty / escalation signals;
- deterministic validation before execution.

Unknown opcodes or malformed programs must fail closed. The runtime must never guess the meaning of an undefined compact symbol.

## Design direction

```text
planner-visible compact codec
        |
        v
codec parser / dictionary resolver
        |
        v
validated semantic AST
        |
        v
Universal Input ISA / reactive runtime
        |
        v
OS / GUI
```

This keeps the compact representation replaceable. The project can later compare text DSLs, binary transports, structured tool calls, or vendor-specific adapters without changing semantic execution.

## Current evidence boundary

The repository now also contains the newer portable-runtime C1 work under `research/runtime_portability_v0/`. That retained experiment is the stronger evidence for the current C1 semantic/wire contract. The older `research/control_codec/` track remains useful as design history and a model-free serialization benchmark, but must not override the newer portable contract or be interpreted as provider-token evidence.

## Research questions

1. How much serialization can be removed before exact model-token accounting is available?
2. What dictionary lifetime gives the best setup-cost / reuse tradeoff?
3. Which operations should remain primitive and which should become semantic methods?
4. Does a compact IR reduce malformed tool output or increase it?
5. How much model-visible output can be removed by persistent methods compared with only shortening primitive syntax?
6. How quickly must methods be invalidated when application state changes?
7. Can the same semantic AST support both human-readable research syntax and a lower-level production codec?

See `../research/control_codec/README.md` for the historical experimental ladder and `../research/runtime_portability_v0/` for the retained portable C1 contract evidence.
