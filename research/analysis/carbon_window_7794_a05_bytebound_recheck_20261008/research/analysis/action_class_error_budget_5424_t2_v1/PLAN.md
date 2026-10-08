# Issue #5424 T2 — typed action-class error budgets

## H/T/D/C/U (frozen before formal execution)

- **H:** In the declared synthetic non-stationary traces, a typed short/long-window route budget plus a separately scoped common-cause parent budget will reduce repeated severe primary-route exposures after an observed fault, while retaining safe-route completion and bounded recovery better than no freeze or a consecutive-failure breaker.
- **T:** Generate one fixed exogenous event corpus with 24 seeds × 192 steps for each of four regimes: stationary transient noise, route-specific drift with repair, one catastrophic event followed by a fault burst and repair, and a shared parent incident spanning two routes. Replay the exact same corpus against `NO_FREEZE`, `LOCAL_CONSECUTIVE_BREAKER`, and `TYPED_MULTIWINDOW_BUDGET`. Preserve every event and each policy decision. Independently replay decisions/metrics from the retained exogenous inputs.
- **D:** Scoped PASS only if the typed controller reduces severe primary exposures after the first signal in drift/catastrophe/common-cause traces versus both comparators; has no common-cause-parent freeze when no incident identity exists; records every route freeze reason and primary/fallback severe outcome; and all affected routes become available within 12 steps after the declared repair boundary. Otherwise report the exact scoped FAIL/HOLD. These are deterministic corpus criteria, not statistical confidence claims.
- **C:** Immediate per-request/cumulative breakers may be safer for high-severity classes; the apparent benefit may be caused by hand-authored thresholds, perfect event attribution, or the simulated read-only probe. If fallback shares the parent fault, budget-triggered rerouting may increase fallback exposure rather than improve outcomes.
- **U:** This synthetic simulator cannot establish real GUI fault distributions, severity weights, attribution quality, non-stationarity, SLO thresholds, safe fallback availability, human impact, production safety, or runtime/product efficacy. Fixed seeds are not population sampling evidence.

## Frozen design

Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

Each replicate has 192 time steps. Routes A/B are assigned by the fixed PRNG. The exogenous corpus records primary outcomes for both routes, alternate-route outcome, shared incident identity, and non-actuating route probes. Regime boundaries are fixed in `experiment.py`; no parameter is tuned after formal invocation.

Policies:

1. `NO_FREEZE`: always use the proposed primary route; after a non-OK result, try the alternate route.
2. `LOCAL_CONSECUTIVE_BREAKER`: freeze only the route with two consecutive severe observed outcomes for 12 steps; then restore on timer.
3. `TYPED_MULTIWINDOW_BUDGET`: severity weights OK=0, transient=1, severe=4, catastrophic=10; route windows 12/48 steps with thresholds 8/16; common-cause parent window 48 steps, charging each affected route once per incident, threshold 8. Freeze for at least 6 steps and require 3 consecutive clean non-actuating probes before restoration.

The simulator records the exogenous primary outcome even while frozen so false-freeze opportunity is measurable. It separately records actually executed primary/fallback outcomes, completion, severe exposure, freeze transitions, and recovery delay. The auditor is a separate implementation over raw input/output JSONL and includes mutation controls.

## Exact frozen invocation

Before invocation, create `research/analysis/action_class_error_budget_5424_t2_v1/raw/formal/` on the host. The exact formal command is:

```sh
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --memory 256m --cpus 1 --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src="$PWD/research/analysis/action_class_error_budget_5424_t2_v1",dst=/work,readonly --mount type=bind,src="$PWD/research/analysis/action_class_error_budget_5424_t2_v1/raw/formal",dst=/results python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /work/experiment.py --out /results
```

The independent auditor runs once in the same pinned image, with the source read-only and the results mount read-write, as `docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --memory 256m --cpus 1 --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src="$PWD/research/analysis/action_class_error_budget_5424_t2_v1",dst=/work,readonly --mount type=bind,src="$PWD/research/analysis/action_class_error_budget_5424_t2_v1/raw/formal",dst=/results python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /work/audit.py /results`.

The formal allocation is one execution of `experiment.py`. Construction smoke tests, if any, must use a distinct output directory and are not formal evidence. Formal inputs/outputs are retained directly through the host bind mount; no claim depends on container-internal IDs.
