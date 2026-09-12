# Research index

Agent Interface is being developed by experiment, not by locking an API early. This file is the evidence ledger for the public repository.

## Research question

Can a strong planner control arbitrary GUI applications through a local interface that:

- works on an unknown app immediately,
- reduces model boundaries and repeated observations,
- learns reusable routes from successful use,
- survives UI/environment drift by invalidating only stale layers,
- and preserves correctness as a hard gate?

## Experimental ladder

### Real Apps v1 — input delivery and sparse observation

Path: [`research/real_apps_v1/`](research/real_apps_v1/)

Apps: XTerm, Chromium, LibreOffice Calc, Inkscape.

What it established:

- fixed `100 ms` sleeps do not guarantee correctness;
- input delivery and application consumption are different events;
- Calc required about `1 ms` character pacing in the tested X11 setup;
- Inkscape long-run drag stability improved when the press-to-motion barrier was increased from the short-screen `2 ms` candidate to `5 ms`;
- sparse/reactive observation can cut full-screen observation substantially while improving success in the development screen.

Primary artifacts:

- [`results/REPORT.md`](research/real_apps_v1/results/REPORT.md)
- [`results/real_app_summary.csv`](research/real_apps_v1/results/real_app_summary.csv)
- [`real_app_suite_v1.py`](research/real_apps_v1/real_app_suite_v1.py)

### Real Apps v2 — semantic method lifetime vs route lifetime

Path: [`research/real_apps_v2/`](research/real_apps_v2/)

Question: when an optimized route fails, should the semantic method be discarded too?

Result: not by default. Across three fresh Inkscape replicates (72 episodes total), keeping the semantic method while suspending/reheating only the route preserved 72/72 success while reducing method redefinition churn, planner-byte proxy, and visual observation.

Primary artifacts:

- [`REAL_APP_SELF_COMPILE_V2_REPORT.md`](research/real_apps_v2/REAL_APP_SELF_COMPILE_V2_REPORT.md)
- [`route_suspend_summary.csv`](research/real_apps_v2/route_suspend_summary.csv)

### Real Apps v3 — Guarded Hierarchical Deoptimization

Path: [`research/real_apps_v3/`](research/real_apps_v3/)

Question: if a fast route has observable dependencies, can we avoid predictable failures before executing the route?

Result: yes, in the tested X11 cases.

- XTerm focus guard: 72/72 success; failed routes eliminated; p99 reduced by about 77.5%.
- Chromium geometry guard: 72/72 success; failed routes eliminated; p99 reduced by about 75.4%.
- Chromium binding replacement + geometry drift: semantic method remained valid while binding was repaired and route deoptimized independently.

Primary artifacts:

- [`GUARDED_HIERARCHICAL_DEOPT_REPORT.md`](research/real_apps_v3/GUARDED_HIERARCHICAL_DEOPT_REPORT.md)
- [`GHD_ALGORITHM_SPEC.md`](research/real_apps_v3/GHD_ALGORITHM_SPEC.md)
- [`guarded_hidden_summary.csv`](research/real_apps_v3/guarded_hidden_summary.csv)
- [`complete_hidden_summary.csv`](research/real_apps_v3/complete_hidden_summary.csv)

## Current hypothesis — Observation Gating

The next major question is whether image feedback can be treated as a local state-change signal rather than automatically forwarding every screenshot to a model.

Candidate ladder:

```text
O0 full screenshot after each step
O1 exact/fast unchanged-frame suppression
O2 + spatial change vector / changed-tile mask
O3 + relevant-region gating
O4 + local VERIFY
O5 + persistent visual state + ROI delta
O6 + GHD deterministic-route observation skip
```

The primary metric should be:

> percentage of model-visible image observations eliminated while preserving the same task correctness.

Secondary metrics: observed pixels, false update detection, missed update, local compute time, tail latency, and escalation rate.

## Parallel hypothesis — Control Codec / Compact IR

The model-to-computer direction has a separate source of waste: repeated control representation.

The project currently measures `planner bytes`, but that proxy should be paired with an explicit experiment on how the same validated control semantics are serialized across the model boundary.

Path: [`research/control_codec/`](research/control_codec/)

Candidate ladder:

```text
C0 verbose structured action list / JSON-like baseline
C1 compact fixed-grammar primitive IR
C2 + persistent opcode / field dictionary
C3 + persistent semantic method references
C4 + short workflow references
C5 + session-local target/state aliases
```

The goal is not to make strings short at any cost. The goal is to remove repeated representation while preserving the same validated semantic AST, guards, retries, held-input state, and recovery behavior.

Until real model/API accounting is available:

- serialization bytes remain a proxy;
- observed pixels / visual bytes remain observation proxies;
- neither may be renamed as tokens.

Actual token-efficiency claims require exact tokenizer/API usage on paired hidden tasks.

Design rationale: [`docs/control-codec.md`](docs/control-codec.md).

## Promotion policy

A candidate is promoted only when:

1. correctness is not worse under the defined hard gate;
2. parameters are frozen before hidden/fresh evaluation;
3. baseline and candidate see the same task/environment schedule;
4. result survives at least one fresh replicate or explicitly remains `HOLD`;
5. claims are scoped to the actual environment measured.

## Claims taxonomy

| Term | Meaning in this repository |
|---|---|
| `planner bytes` | serialization byte proxy, **not tokens** |
| `observed pixels` | pixels captured/processed by the harness, **not image tokens** |
| `wall time` | local harness timing, **not model-in-loop latency** |
| `hidden/fresh` | task/seed not used to tune the candidate; not a security claim |
| `real app` | actual desktop application under X11/Xvfb, not a synthetic widget model |

## Rejected or held ideas

Negative results are retained because they constrain the design space.

- fixed sleeps as a correctness mechanism — rejected;
- method-wide invalidation for every route failure — rejected as default;
- blind re-anchor-and-continue — unstable in fresh runs;
- aggressive predicted ROI without clipped-observation rejection — caused centroid bias/failures;
- event filtering across a high-frequency Python/stdio boundary — observer overhead erased gains;
- replacing all observation with a single global perceptual hash — insufficient for local motion/change.

## Next experiments

1. Observation Gating on the real-app suite.
2. Control Codec primitive-serialization baseline (`C0` vs `C1`) using the same Universal Input semantics.
3. Dictionary/method-reference amortization: include definition, invalidation, and relearning cost rather than only invocation length.
4. Multi-resolution image change vectors vs global hashes.
5. Automatic guard placement: compare guard cost against expected stale-route failure cost.
6. Longer mixed-app sessions with app restarts, focus drift, geometry drift, and modal transitions.
7. When a real model endpoint is available, replay the same hidden schedules and replace byte proxies with exact text/image token accounting.
8. Only after algorithmic semantics stabilize: production-oriented implementation work.
