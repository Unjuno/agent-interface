# Design Theses and Idea Ledger

This file records the main system ideas that shape Agent Interface and distinguishes promoted evidence from active or proposed work.

It is not a claims page. Promotion still depends on the experiment reports under `research/`.

## Status vocabulary

- **Promoted** — supported by the repository's current evidence and reflected in the architecture.
- **Active** — currently being benchmarked; not yet a general claim.
- **Proposed** — design hypothesis worth testing.
- **Deferred** — intentionally postponed until a dependency or measurement boundary is ready.

## 1. Interface bottleneck thesis

**Status: Promoted as the project's research thesis, not proven universally.**

For a sufficiently capable planner, computer-control cost can be dominated by interface mechanics: repeated model boundaries, redundant observations, verbose serialization, input-delivery waits, recovery, and relearning.

The clean experiment holds the model, task, environment, and correctness requirement fixed and changes only the interface.

## 2. Universal fallback before specialization

**Status: Promoted.**

Unknown applications must remain operable through keyboard, pointer, text, focus, observation, and reactive verification. Application methods are optimizers over Universal Control, not prerequisites.

## 3. Self-compiling application methods

**Status: Active / partially supported.**

Repeated successful traces should not be replanned forever. The system should be able to retain a semantic method while independently optimizing or invalidating its execution route.

Long-term target:

```text
primitive input
  -> universal reactive program
  -> application method
  -> short workflow method
```

A failed route should normally deoptimize before invalidating the semantic method.

## 4. Prefer cheap deterministic input routes

**Status: Proposed / partially exercised in research harnesses.**

If an application operation can be completed reliably through a keyboard shortcut, command sequence, or other deterministic input route, repeatedly locating the equivalent GUI button is unnecessary work.

The route selector should compare correctness, observation requirements, delivery semantics, and lifecycle stability rather than assume pointer interaction is the default.

## 5. Control Codec / high-density model-to-computer IR

**Status: Active research track.**

The project originally focused on reducing repeated control representation as well as reducing observations. That idea is now explicit again.

Candidate progression:

```text
verbose structured actions
  -> compact primitive IR
  -> persistent opcode/field dictionary
  -> semantic method references
  -> workflow references
  -> session-local target/state aliases
```

The largest expected gain is persistent shared structure, not merely single-character opcodes.

All compact representations must resolve to the same validated semantic AST. See `control-codec.md` and `../research/control_codec/`.

## 6. Observation Gating

**Status: Active research track.**

Computer-to-model traffic should cross the model boundary only when it contains new task-relevant information.

Candidate progression:

```text
full frame
  -> unchanged-frame suppression
  -> changed-tile / spatial delta
  -> relevant-region gating
  -> local VERIFY
  -> persistent visual state + ROI delta
  -> deterministic-route observation skip
```

Ordinary visual state may be lossy/latest-only; semantic barriers and errors must remain reliable.

## 7. Incremental / streaming feedback

**Status: Proposed; API/model-in-loop measurement still required.**

The interface should not force the planner to wait for a fixed sleep or a complete screenshot if a trustworthy acknowledgement, state change, or compact verification result is already available.

A future model adapter may support incremental feedback and action patch/cancel semantics. This must be measured with the actual model API before any frequency or latency claim is made.

## 8. Guard speculative actions with state versions

**Status: Architectural principle / active design.**

Any action queued against an older semantic state must be rejectable before execution.

```text
action.base_state_version != runtime.state_version
    -> cancel / replan
```

Speculation without a stale-action guard can trade latency for silent mis-execution.

## 9. Keep high-frequency deterministic loops local

**Status: Promoted principle.**

Input delivery, update detection, local verification, retry, and fine motor correction should not cross a remote/model boundary when semantic reasoning is unnecessary.

MCP/HTTP/vendor adapters may exist outside the hot path. The production transport should be chosen after measuring boundary-crossing cost and required call frequency.

## 10. Closed-loop fine motor control

**Status: Experimental.**

Pointer displacement and on-screen object displacement are not always identical, especially in 3D/CAD-like interaction. Precision manipulation may require local visual feedback instead of a single open-loop drag.

Important sub-principle: cache a static target at gesture start when the moving object can occlude it; track the moving handle rather than repeatedly re-estimating an occluded target.

## 11. Layered lifetimes and narrow invalidation

**Status: Promoted.**

Different knowledge layers fail at different rates:

```text
semantic meaning
binding
action precondition
optimized route
observation cache
motor calibration
```

Invalidate the narrowest stale layer. Do not relearn semantic meaning merely because geometry or focus changed.

## 12. Event-driven observation over polling

**Status: Experimental baseline / promoted principle where measured.**

Polling a screen that has not changed creates cost without new information. Prefer backend update events plus targeted observation when the backend can provide them reliably.

## 13. No mandatory local neural model

**Status: Current scope constraint.**

The core research question is interface design, not whether another local VLM/policy can compensate for a weak interface. The runtime should therefore remain deterministic unless future evidence shows a local learned component is necessary and its dependency cost is justified.

## 14. Benchmark integrity is part of the system design

**Status: Promoted research discipline.**

Known benchmark failure modes include:

- public seed / PRNG prediction;
- DOM/internal target leakage;
- changing the task environment while claiming observation compression;
- stale-frame use;
- oracle recovery;
- privileged session/version markers;
- optimizing means while hiding p95/p99 regressions.

Use paired hidden schedules, hard correctness gates, fresh replicates, and separate measured values from proxies.

## 15. Actual token efficiency remains unmeasured

**Status: Deferred pending real model/API integration.**

`planner bytes` are useful for serialization experiments but are not tokens. `observed pixels` are not image tokens. Real claims require exact model/API accounting on paired hidden tasks.

The Control Codec track exists partly to make that future measurement explicit rather than leaving token efficiency implicit.

## Current priority order

1. Observation Gating on real applications.
2. C0 vs C1 Control Codec baseline on the same Universal Input semantics.
3. Dictionary/method/workflow amortization including definition and invalidation cost.
4. Longer mixed-app sessions and automatic guard policy.
5. Consolidate promoted semantics into the runtime workspace.
6. Real model-in-loop token and feedback-latency measurement once the interface semantics are stable enough to make the comparison meaningful.
