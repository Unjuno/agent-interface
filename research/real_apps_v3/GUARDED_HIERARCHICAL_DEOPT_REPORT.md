# Guarded Hierarchical Deoptimization — Real-App Iteration Report

## Scope

This iteration tests whether a self-compiling Agent Interface should keep different lifetimes for semantic methods, target bindings, repairable preconditions, and optimized routes.

Environment:

- Debian 13 container
- Xvfb 1280×800×24 + Openbox
- X11 XTEST
- XTerm 398
- Chromium 144.0.7559.96
- Inkscape 1.4 evidence carried forward from `real_apps_v2`
- controller-visible state limited to public X11/GUI observations

All byte measurements are serialization proxies, not model tokens. Local wall time is not model-in-loop latency.

## 1. Route lifetime is shorter than semantic-method lifetime

The v2 Inkscape result was reproduced across XTerm and Chromium: when an optimized route becomes stale, retaining the semantic method and suspending only the route preserves correctness while reducing relearning/observation churn.

| app | invalidate correctness | route-suspend correctness | method defs/run | planner-byte reduction | observed-pixel reduction |
|---|---:|---:|---:|---:|---:|
| Inkscape | 72/72 | 72/72 | 3.33 → 1.00 | 27.8% | 51.9% |
| XTerm | 72/72 | 72/72 | 3.00 → 1.00 | 11.0% | 66.7% |
| Chromium | 72/72 | 72/72 | 3.00 → 1.00 | 12.7% | 44.4% |

Wall-time changes from route suspension alone were noisy and are not promoted as a speed claim.

## 2. Target binding is a separate lifetime

Chromium sessions contained two independent perturbations:

1. visible window-geometry drift at episode 8, invalidating an absolute omnibox route;
2. real browser replacement at episode 16, forcing the runtime to discover a new live X11 window binding.

Three policies were compared over three fresh 24-episode runs each.

| policy | correctness | semantic defs/run | semantic invalidations/run | planner B/ep | observed MPix/ep |
|---|---:|---:|---:|---:|---:|
| route/binding failure kills method | 72/72 | 3 | 2 | 44.51 | 0.427 |
| binding failure kills method | 72/72 | 2 | 1 | 41.69 | 0.341 |
| layered binding repair | **72/72** | **1** | **0** | **38.88** | **0.256** |

A replaced window instance is not evidence that the semantic method itself changed.

## 3. Pre-execution guards avoid predictable failures

A stale fast route is expensive when the runtime executes it, waits for a verification timeout, and only then falls back. The next candidate therefore evaluates cheap observable dependencies before the route is executed.

### XTerm focus guard

External focus loss was injected twice per session. The guarded policy checks `_NET_ACTIVE_WINDOW`; wrong focus is repaired idempotently without cooling the route.

Three fresh 24-episode runs per strategy:

| metric | unguarded | guarded |
|---|---:|---:|
| correctness | 72/72 | **72/72** |
| failed fast routes/run | 2 | **0** |
| input events/ep | 17.33 | **16.00** |
| p50 | 15.39 ms | 15.31 ms |
| p95 | 42.96 ms | **33.74 ms** |
| p99 | 166.50 ms | **37.45 ms** |

Mean paired reductions: p95 ≈21.5%, p99 ≈77.5%, physical input events ≈7.7%.

### Chromium geometry guard

The optimized route stores an absolute omnibox click coordinate, so window geometry is a true dependency. If geometry differs from calibration geometry, the route is deoptimized before the stale click and Universal `Ctrl+L` navigation is used instead.

Three fresh 24-episode runs per strategy:

| metric | unguarded | guarded |
|---|---:|---:|
| correctness | 72/72 | **72/72** |
| failed fast routes/run | 2 | **0** |
| input events/ep | 50.67 | **46.75** |
| p50 | 103.51 ms | 104.71 ms |
| p95 | 212.85 ms | **156.26 ms** |
| p99 | 653.74 ms | **160.93 ms** |

Mean paired reductions: p95 ≈26.6%, p99 ≈75.4%, physical input events ≈7.7%. Median latency did not improve; the gain is tail avoidance.

## 4. Complete hierarchy in one Chromium session

The final comparison combined geometry drift at episode 8 and forced browser/window-binding replacement at episode 16. Both policies already retained semantic methods and repaired bindings; only the guarded policy checked fast-route geometry before execution.

Three fresh 24-episode runs per policy:

| metric | layered, unguarded route | GHD |
|---|---:|---:|
| correctness | 72/72 | **72/72** |
| method definitions/run | 1 | 1 |
| semantic invalidations/run | 0 | 0 |
| binding repairs/run | 1 | 1 |
| failed route executions/run | 1 | **0** |
| guard DEOPTs/run | 0 | 1 |
| planner bytes/ep | 38.83 | 38.83 |
| observed MPix/ep | 0.256 | 0.256 |
| p50 | **106.96 ms** | 108.11 ms |
| p95 | 211.69 ms | **166.29 ms** |
| p99 | 235.29 ms | **202.09 ms** |

Relative to the same layered hierarchy without the route guard: p50 regressed ≈1.1%, p95 improved ≈21.4%, p99 improved ≈14.1%, with no observed correctness loss and no extra image observation/planner serialization.

Raw summaries are in [`guarded_hidden_summary.csv`](guarded_hidden_summary.csv) and [`complete_hidden_summary.csv`](complete_hidden_summary.csv).

## 5. Promoted candidate

```text
Semantic Method                         long-lived
    |
    +-- Target Binding                  repairable cache
    |      stale -> rediscover/rebind, keep method
    |
    +-- Repairable Preconditions        ephemeral state
    |      e.g. focus -> repair idempotently
    |
    +-- Optimized Route                 invalidatable cache
    |      guard stale dependencies before execution
    |      stale -> DEOPT -> Universal fallback
    |      reheat after 2 clean uses
    |
    +-- Universal Route                 correctness floor
           fresh binding + Universal failure
           -> only then escalate semantic invalidation
```

Working rule:

> Do not wait for a predictable fast-path failure. Guard dependencies before execution, and invalidate or repair the smallest independently verifiable layer.

## 6. Error check

Results discarded during development are not included in the promoted tables:

- an early XTerm fixture had an input/title mismatch;
- an early Chromium restart test did not force a distinct live X11 window id;
- route-suspension wall-time wins that did not reproduce stably were not promoted.

The report was corrected after publication of `v0.0.1-research.1`; `v0.0.1-research.2` is the first recommended research snapshot for this result.

## 7. H / T / D / C / U

**H:** explicit observable route dependencies plus separate cache lifetimes preserve semantic knowledge while avoiding predictable stale-route failures.

**T:** real X11 applications, XTEST input, three fresh replicates per principal comparison, controller-unrevealed focus/geometry/binding perturbations, correctness as a hard gate.

**D:** **PASS** for the next Python experimental baseline. GHD preserved 100% observed correctness in the reported hidden runs and materially reduced tail latency.

**C:** guards can be expensive, incomplete, or overly sensitive. Visual guards will be noisier than exact X11 focus/geometry guards.

**U:** external validity remains limited to X11 and the tested applications. The strongest current guards use exact X11 metadata.

## 8. Next experiment

Observation Gating and automatic guard selection are now higher-value than further timeout tuning: measure when a pre-execution guard is cheaper than the expected cost of executing a stale route, and suppress model-visible images when no relevant new visual information exists.
