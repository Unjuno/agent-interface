# Guarded Hierarchical Deoptimization — Real-App Iteration Report

## Scope

This iteration continues the original self-compiling Agent Interface research using Python as the experimentation layer. Rust migration remains deferred until the algorithm is stable.

Environment:

- Debian 13 container
- Xvfb 1280x800x24 + Openbox
- X11 XTEST
- XTerm 398
- Chromium 144.0.7559.96
- Inkscape 1.4 results imported from real_apps_v2
- Controller-visible signals: screenshots/ROI, focus, window title, window geometry, X11 window existence
- Hidden evaluation/oracles are not exposed as route-selection inputs

## 1. Cross-application reproduction of route suspension

Prior Inkscape result: keep the semantic method, suspend only its optimized route, run Universal fallback inside the method, and reheat after two clean uses.

Fresh hidden replication extended this to XTerm and Chromium.

| app | correctness invalidate | correctness route-suspend | method defs/run invalidate -> suspend | planner bytes reduction | observed pixels reduction |
|---|---:|---:|---:|---:|---:|
| Inkscape | 72/72 | 72/72 | 3.33 -> 1.00 | 27.8% | 51.9% |
| XTerm | 72/72 | 72/72 | 3.00 -> 1.00 | 11.0% | 66.7% |
| Chromium | 72/72 | 72/72 | 3.00 -> 1.00 | 12.7% | 44.4% |

Wall-time changes for XTerm/Chromium were noisy and are not promoted as a speed claim. The stable result is reduced relearning/serialization/observation with unchanged observed correctness.

## 2. Split target binding from semantic method identity

Chromium session contained two independent perturbations:

1. episode 8: visible browser geometry drift, invalidating an absolute omnibox click route;
2. episode 16: real browser replacement. A second Chromium instance was created first to force a distinct X11 window id; only then was the old browser destroyed. The controller was not given the new id and had to rediscover it from observable X11 state.

Three policies were compared in three fresh 24-episode runs each.

| policy | correctness | semantic defs/run | semantic invalidations/run | planner B/ep | observed MPix/ep |
|---|---:|---:|---:|---:|---:|
| coarse: route/binding failure kills method | 72/72 | 3 | 2 | 44.51 | 0.427 |
| binding failure kills method | 72/72 | 2 | 1 | 41.69 | 0.341 |
| layered binding repair | 72/72 | **1** | **0** | **38.88** | **0.256** |

There was no stable wall-time dominance in this test. The result supports a separate binding lifetime: a replaced window instance is not evidence that the semantic method itself changed.

## 3. Pre-execution dependency guards

Failure-after-the-fact still produced long latency tails because the runtime executed a known-stale fast path and waited for verification timeout. The next candidate therefore attached observable dependencies to optimized routes.

### XTerm focus precondition

The hot route assumes the target terminal already has focus. External focus loss was injected twice per session.

Guarded policy:

- check `_NET_ACTIVE_WINDOW` before dependent input;
- if focus is wrong, repair focus idempotently;
- keep the optimized route hot; do not invalidate or reheat it.

Three fresh 24-episode runs per strategy:

| metric | unguarded | guarded |
|---|---:|---:|
| correctness | 72/72 | 72/72 |
| failed fast routes/run | 2 | **`0`** |
| input events/ep | 17.33 | **16.00** |
| p50 | 15.39 ms | 15.31 ms |
| p95 | 42.96 ms | **33.74 ms** |
| p99 | 166.50 ms | **37.45 ms** |

Mean paired reductions: p95 ~21.5%, p99 ~77.5%, physical input events ~7.7%.

### Chromium geometry dependency

The optimized route stores an absolute omnibox click coordinate. Browser geometry is therefore a true route dependency.

Guarded policy:

- compare current observable geometry to the geometry under which the route was calibrated;
- if it differs, DEOPT before executing the stale click;
- run Universal `Ctrl+L` fallback;
- reheat/recalibrate the route after two clean uses.

Three fresh 24-episode runs per strategy:

| metric | unguarded | guarded |
|---|---:|---:|
| correctness | 72/72 | 72/72 |
| failed fast routes/run | 2 | **`3`** |
| input events/ep | 50.67 | **46.75** |
| p50 | 103.51 ms | 104.71 ms |
| p95 | 212.85 ms | **156.26 ms** |
| p99 | 653.74 ms | **160.93 ms** |

Mean paired reductions: p95 ~26.6%, p99 ~75.4%, physical input events ~7.7%. Median latency did not improve and slightly regressed on average; the gain is tail avoidance.

## 4. Complete hierarchy in one real Chromium session

Final comparison combined both perturbation classes in one session:

- geometry drift at episode 8;
- forced X11 binding replacement/browser restart at episode 16.

Both policies already used semantic-method retention and binding repair. The only difference was whether the absolute fast route had a pre-execution geometry guard.

Three fresh 24-episode runs per policy:

| metric | layered, unguarded route | Guarded Hierarchical Deoptimization |
|---|---:|---:|
| correctness | 72/72 | **72/72** |
| method definitions/run | 1 | **1** |
| semantic invalidations/run | 0 | **`0`** |
| binding failures repaired/run | 1 | **1** |
| failed route executions/run | 1 | **0`** |
| guard DEOPTs/run | 0 | 1 |
| planner bytes/ep | 38.83 | 38.83 |
| observed MPix/ep | 0.256 | 0.256 |
| p50 | **106.96 ms** | 108.11 ms |
| p95 | 211.69 ms | **166.29 ms** |
| p99 | 235.29 ms | **202.09 ms** |

Relative to the same layered hierarchy without the route guard:

- p50: ~1.1% regression;
- p95: ~21.4% reduction;
- p99: ~14.1% reduction;
- no observed correctness loss;
- no additional image observation or planner serialization.

## 5. Candidate algorithm

Promote to the next experimental baseline:

```text
Semantic Method                        long-lived
    |
    +-- Target Binding                  repairable cache
    |      guard: target exists / matches public identity
    |      failure: rediscover/rebind, keep method
    |
    +-- Repairable Preconditions        ephemeral state
    |      e.g. focus
    |      guard: cheap observable state
    |      failure: repair idempotently, keep route hot
    |
    +-- Optimized Route                 invalidatable cache
    |      dependencies: geometry / visual anchor / mode / shortcut validity
    |      guard failure: pre-execution DEOPT, Universal fallback
    |      reheat: 2 clean uses
    |
    +-- Universal Route                 correctness fallback
           if fresh binding + Universal route fails postcondition:
               escalate toward semantic invalidation/relearning
```

Working rule:

**Do not wait for a predictable fast-path failure. Guard dependencies before execution, and invalidate/repair the smallest independently verifiable layer.**

## 6. What was rejected or corrected during this iteration

- An initial XTerm fixture reported 0/24 success because uppercase synthetic input did not match the expected title. The fixture result was discarded and corrected before strategy comparison.
- An initial Chromium restart test did not guarantee a new X11 window id because resource ids can be reused after client exit. Those numbers were discarded. The final benchmark creates the replacement browser before killing the old one, guaranteeing a distinct live id.
- Wall-time improvements from route suspension alone were not stable across Chromium runs; only serialization/observation reductions are promoted for that stage.
- Guarded routes improve tail latency substantially but do not improve p50 consistently. Claims are separated accordingly.

## 7. H / T / D / C / U

### H
A self-compiling Agent Interface should attach explicit observable dependencies to optimized routes and maintain separate lifetimes for semantic methods, application bindings, repairable preconditions, and optimized routes.

### T
Real X11 applications, actual synthetic HID input, three fresh hidden replicates per principal comparison, externally injected but controller-unrevealed focus/geometry/binding perturbations, correctness as a hard gate.

### D
PASS for promotion to the next Python experimental baseline. Guarded Hierarchical Deoptimization preserved 100% observed correctness in the reported hidden runs and materially reduced tail latency while retaining the serialization/observation benefits of layered cache invalidation.

### C
A guard can itself become expensive, incomplete, or over-sensitive. Visual-anchor dependencies will be noisier than exact X11 focus/geometry guards. A false-negative guard reintroduces timeout tails; a false-positive guard may over-DEOPT and lose amortization.

### U
External validity remains limited to X11 and the tested apps. The strongest guard results use exact X11 metadata. Future tests must cover visual-only guards, mode changes, semantic-method mutation, longer mixed sessions, and ultimately Wayland/macOS/Windows backends.

## 8. Next experiment

The next high-value experiment is not another timeout tweak. It is a **dependency-guard classifier**:

1. exact system guard (focus/window existence/geometry),
2. visual guard (anchor/ROI signature),
3. postcondition-only verification when no cheap precondition guard exists.

Measure false-positive/false-negative deopt rates under noise and determine when a guard is worth evaluating versus simply executing the route.
