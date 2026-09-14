# Architecture

## First-principles objective

Agent Interface minimizes total agent-computer control cost subject to a hard correctness constraint.

The target cost is not just mouse latency. It includes:

- model boundaries,
- model-visible serialization,
- image/observation bandwidth,
- local execution overhead,
- retries and recovery,
- relearning after environment changes.

## Current stack

```text
User intent
    |
    v
Strong planner / LLM
    |
    | semantic goal / method call / short program
    v
+---------------------------------------------+
| Agent Interface                              |
|  semantic methods                            |
|  short workflow methods                      |
|  universal fallback                          |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| Guarded Hierarchical Runtime                 |
|  target binding                              |
|  repairable preconditions                    |
|  optimized route cache                       |
|  observation policy                          |
|  motor calibration                           |
|  retry / deopt / reheat                      |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| Universal Reactive Control                   |
|  acquire / verify / wait-update / fallback   |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| Universal Input ISA                          |
|  keyboard / text / pointer / drag / scroll   |
|  focus / observation                         |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| Local backend                                |
|  delivery semantics / event processing       |
|  image-change feedback / visual servo        |
+----------------------+----------------------+
                       |
                       v
                    OS / GUI
```

## Universal control is the floor

An unknown application must be controllable without an app-specific API. App methods are optimizers over universal control, not replacements for it.

The system should therefore always preserve a generic fallback route based on keyboard, pointer, text, focus, observation, and reactive verification.

## Semantic method and optimized route are different objects

A semantic method can remain valid while its fastest execution route becomes stale.

Example:

```text
SAVE_DOCUMENT
  semantic meaning      long-lived
  target binding        medium-lived
  focus precondition    repairable
  shortcut route        potentially stale
  visual anchor         potentially stale
  observation policy    potentially stale
```

Invalidating all layers together creates unnecessary relearning.

## Guarded Hierarchical Deoptimization (GHD)

The current candidate lifecycle:

```text
invoke semantic method
    |
    v
binding guard
    | stale -> rediscover/rebind, keep method
    v
repairable precondition guard
    | focus/mode invalid -> repair, keep route if dependency still valid
    v
optimized-route dependency guard
    | stale -> deopt route before execution
    v
execute route or universal fallback
    |
    v
verify semantic effect
    | route failure -> route cold + fallback
    | universal failure with fresh binding -> escalate semantic invalidation
    v
2 clean fallback uses -> route may reheat
```

This is analogous to guarded speculation and deoptimization in JIT systems: retain semantic knowledge, invalidate the narrowest stale optimization.

## Observation architecture

The next research layer is Observation Gating.

The intended escalation path is:

```text
OS/semantic event?
    no -> no observation
    yes
      |
frame changed?
    no -> do not send image
    yes
      |
relevant region changed?
    no -> suppress
    yes
      |
local verification sufficient?
    yes -> return compact event/result
    no
      |
send changed ROI
      |
uncertain -> full-frame escalation
```

The key distinction is between *screen changed* and *agent-relevant information changed*.

## Input delivery semantics

Sending an OS event is not equivalent to the application consuming it or completing its semantic effect. The X11 experiments therefore treat input delivery, observable state change, and semantic verification as distinct boundaries.

Backend-specific pacing/barrier values must remain backend policy rather than leaking into semantic methods.

## Coordinate frames and binding resolution

An absolute screen point is incomplete when a program can move between window
geometries. Application chrome and window content may follow different
transforms. A pointer intent should therefore declare the coordinate frame and
the source binding on which its points were authored.

The current research candidate resolves the complete program against the latest
stable target binding before validation:

```text
source point + explicit frame + source geometry
    |
    v
latest target focus / surface / geometry
    |
    v
frame-specific translation
    |
    v
whole-program validation
    |
    v
runtime focus / surface / geometry / hit checks
    |
    +-- mismatch -> needs_decision before pointer admission
    v
input
```

Resolution itself grants no authority. Frame identity is still task-declared in
the current evidence; observed-region identity, internal scrolling, scaling and
automatic fallback remain research problems.

## Implementation strategy

The current implementation language for experiments is Python because algorithmic semantics are still changing rapidly. A lower-level systems implementation is intentionally deferred until the algorithms, error semantics, and protocol boundaries are substantially frozen.

The research code should therefore optimize for falsifiability and iteration speed now, not premature ABI stability.
