# Issue #5366 T2 — semantic effects vs resource interference

## H/T/D/C/U

- **H:** A semantic-only `read(ui)` effect row can admit an observation whose occupancy of a shared serialized resource delays a controller past its deadline. A separate resource-interference envelope can reject/defer only over-budget and unknown reads while retaining known-benign reads.
- **T:** Five finite synthetic observations (fast, slow, cache hit, cache miss, unknown envelope) each run through three frozen policies: semantic-only, reject-all-observations, and semantic-plus-resource. A controller arrives at time 0, needs 1 ms service, and must complete by 2 ms; each observation starts 1 ms before it. No real timing or external effect is invoked.
- **D:** `PASS_METHOD_SCOPED` only if an independent raw-only auditor reconstructs all 15 policy/case rows, resource-aware admission allows the fast/cache-hit cases, denies the slow/cache-miss cases, keeps the unknown envelope `UNKNOWN` and non-admitted, yields no late controller completion, and rejects all five mutations. Semantic and resource effects must remain separate dimensions.
- **C:** Runtime scheduling, serialization, or measurement could dominate a static resource row; blanket rejection might be preferable under a stricter safety contract; a measured envelope could age out under changed load.
- **U:** Hand-authored durations and a single-server queue do not establish real X11/AT-SPI costs, workload frequency, a portable timing bound, or GUI behavior. This does not prove effect-row soundness, runtime safety, or product benefit.

## Freeze and execution rule

The base is pinned in `FREEZE.json`. Candidate and auditor each run exactly once, with zero retry; formal raw output is a different file from construction tests. The auditor imports neither candidate nor its helpers. A construction defect before the formal invocation is corrected and logged; after a formal candidate starts, preserve all failures without rerunning.

The host runs CPython on macOS arm64. OrbStack's Engine is responsive, but an owner-unknown shared container is active and repository Issue #5085 does not authorize a second container. No container is touched or started. This fixture has no container-specific semantics.

## Exact estimand

For each case, the read begins at `t=-1 ms`, and a controller needing `1 ms` arrives at `t=0`. If the read is admitted, controller completion is `max(0, read_duration - 1) + 1`; otherwise it is `1`. Deadline is `2 ms`. A case is late iff completion exceeds 2 ms. The declared resource upper bound—not the latent duration—is the resource-aware gate input. An absent bound must remain `UNKNOWN`.

No candidate may access the `actual_service_ms` field for admission; it is oracle-only input used to score the resulting queue schedule.
