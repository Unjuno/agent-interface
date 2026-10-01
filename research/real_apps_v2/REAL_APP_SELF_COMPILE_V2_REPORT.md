# Real-App Self-Compiling Interface v2

## Purpose

Return to the original Agent Interface hypothesis on a real GUI: Universal Control must work cold, repeated successful traces should become methods, and failures should self-heal without discarding more learned structure than necessary.

## Environment

- Debian 13 container
- Xvfb 1280x800x24 + Openbox
- Inkscape 1.4
- X11 XTEST input
- Controller observation: screenshot/ROI only
- Success oracle: saved SVG geometry, not exposed to controller

## Primitive hardening before the higher-level test

A short 20-trial microbench had suggested a 2 ms ButtonPress->motion dwell was sufficient. A 30-episode long-session audit falsified that conclusion: 2 ms required 14 local retries, while 5 ms and 10 ms both completed 30/30 with zero retry. 5 ms was retained as the lower-latency stable baseline.

Effect verification was also changed from an exact predicted-endpoint ROI to a swept ROI covering the union of the pre-drag target and nominal endpoint. This removed false semantic failures when motor gain varied slightly.

## Main algorithmic comparison

### A. Whole-method invalidation (v4-style coarse policy)

On an acquisition/route failure, discard the learned method fast path; execute Universal fallback; require two clean uses before defining/promoting the method again.

### B. Route suspension (candidate)

Separate two lifetimes:

1. semantic method symbol / parameterization
2. optimized local route/anchor cache

On a route failure, keep the semantic method callable, immediately suspend only the optimized route, execute Universal fallback inside the method, and require two clean uses before reheating the route. No new model-visible method definition is required.

## Fresh hidden audit

Three independent 24-episode runs per strategy. Each session contains visible zoom+ / zoom- perturbations unknown to the controller.

| Metric | whole-method invalidate | route suspend |
|---|---:|---:|
| total correctness | 72/72 | **72/72** |
| mean method definitions / run | 3.33 | **1.00** |
| mean invalidations / run | 2.67 | **1.00 route suspension** |
| planner bytes / episode | 33.29 B | **24.04 B** |
| observed pixels / episode | 0.847 MPix | **0.407 MPix** |
| mean p50 task wall | 168.8 ms | **168.1 ms** |
| mean p95 task wall | 322.4 ms | **176.3 ms** |
| worst-run p95 | 591.0 ms | **177.8 ms** |

Relative to whole-method invalidation, route suspension reduced mean planner serialization by **27.8%** and observed pixels by **51.9%**, with no observed correctness loss. Median latency is essentially unchanged; the gain is primarily reduced recovery churn and much tighter tail latency.

## Reheat tuning

Initial method learning remained fixed at two successful uses. Route reheat after a suspension was tested at 1, 2, and 3 clean uses with three Latin-square ordered replicates each. All settings achieved 72/72 success.

| route reheat | mean observed MPix/ep | worst p95 | worst p99 | decision |
|---:|---:|---:|---:|---|
| 1 clean use | **0.366** | 178.0 ms | 188.1 ms | HOLD |
| 2 clean uses | 0.396 | **175.6 ms** | **179.0 ms** | **PROMOTE** |
| 3 clean uses | 0.521 | 184.9 ms | 186.9 ms | REJECT |

The original v4 `2 clean uses` recalibration value therefore remains the best robustness/tail choice in this real-app test. The improvement is not the threshold; it is the granularity of invalidation.

## New design rule

**Invalidate aggressively, but invalidate the smallest independently verifiable layer.**

Hierarchy:

```text
semantic method definition        long-lived
        |
        +-- optimized route       invalidatable
        +-- visual anchor/cache   invalidatable
        +-- motor calibration     invalidatable
```

A visual anchor miss should not force the planner to forget a valid semantic operation. Conversely, blindly preserving the hot route after an anchor miss was tested and rejected because it produced unstable semantic/effect failures.

## H / T / D / C / U

**H**: splitting method identity from route-cache validity preserves correctness while reducing relearning/serialization and recovery observation.

**T**: real Inkscape process, actual XTEST input, two hidden UI perturbations per 24-episode session, three fresh replicates per main strategy; separate route-reheat 3x3 audit.

**D**: PASS for this application/backend. Promote `route suspension + 2 clean uses` to the next multi-app candidate. Reject blind local re-anchor as a general policy.

**C**: gains may shrink for methods whose fallback route is expensive or whose semantic meaning really changes with UI state. A true app update may invalidate method semantics, not merely its route.

**U**: external validity is still limited to Inkscape/X11 for this policy. Next gate is cross-application reproduction on Calc and Chromium plus synthetic stress where method semantics themselves change.
