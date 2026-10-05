# Issue #7383 — freshness-gated observation hedging T0

Status: **`PASS_METHOD_SCOPED`** for the frozen deterministic T0; real capture adoption remains HOLD.

## H / T / D / C / U

**H.** In the explicitly declared independent heavy-tail fixture, one delayed duplicate of a read-only observation can reduce p95 complete-current-observation latency by at least 10%, while duplicate work stays within 1.20 times baseline primary work and the independently scored deadline outcome does not worsen. Strongly correlated delay, a serialized shared queue, delayed cancellation, and generation changes may erase the benefit or require a fail-closed yield.

**T.** Use the finite deterministic service-time and mutable-generation cases in `spec.json`. Derive the hedge delay only from a disjoint calibration deck. Compare one request, a delayed single hedge, and immediate duplication. The candidate emits full request, capture, completion, cancellation, work, epoch and consumer records. A separate auditor reconstructs them without importing candidate code, checks p50/p95/p99, admission/freshness/uniqueness and duplicate-work accounting, and rejects four preregistered corruptions. No model, action, GUI, network or outcome data are used.

**D.** `PASS_METHOD_SCOPED` requires exact candidate/auditor agreement for every row, all four corruption controls rejected, no stale/partial/double admission, complete loser-work accounting, and the declared heavy-tail p95/work/deadline criteria. No result is a deployment recommendation. A result that meets the criteria only in the planted independent-service case does not imply benefit under real capture workloads.

**C.** The test can be favorable because its independent secondary service is intentionally uncorrelated with the primary tail. Real capture workers may share a serialized compositor, queue, lock, encoder, or source-generation race; then duplication can add load without reducing latency. If captures are not a measured critical path, there is no reason to hedge them.

**U.** Deterministic synthetic timings establish only simulator/auditor behavior. They do not establish a real observation straggler, X11/Xvfb behavior, Windows/macOS capture performance, reduced end-to-end latency, application-effect non-interference, task benefit, safety, or adoption value. A T1 would need fresh authorization and a private disposable fixture.

## Execution and provenance

- Issue: [#7383](https://github.com/Unjuno/agent-interface/issues/7383)
- Allocation: `GUI-OBSERVATION-HEDGING-7383-T0-20261004-A01`
- Intended evidence path: `research/analysis/observation_hedging_7383_t0_20261004/`
- Source main: `13bab54ea6d91978247ecc1b70e5060db752367a`.
- Runtime: host CPython 3.14.5, macOS 27.0.1 arm64. OrbStack returned `containerd` missing blob / `operation not supported` on inventory; no repeated check or container run is claimed.
- Invocation budget after preregistration: one candidate, one independent auditor, zero retries.

Formal A01 commands each ran once and exited 0; the independent audit reports `PASS_METHOD_SCOPED`, 1,000/1,000 rows reconstructed and four mutations rejected. Construction tests passed 6/6. Exact exits, outputs and hashes are retained in `RUN_RECORD.json`, `results/`, and `SHA256SUMS.txt`. These are synthetic method results only; no current observation critical-path or task-effect claim follows.
