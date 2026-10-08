# Issue #16 T4 — interrupted-prefix policy comparison

## H / T / D / C / U

**H.** On identical deterministic interruption prefixes, explicit saga decomposition with verified compensators converts some non-empty, fully compensatable prefixes from baseline `UNKNOWN` to `ABORTED_COMPENSATED`, while preserving the historical effects and leaving prefixes containing an irreversible effect `ABORTED_PARTIAL`. It must never report `COMMITTED` on an interrupted prefix.

**T.** Three fixed action schedules: four all-reversible actions; reversible actions around an irreversible `SEND`; and an irreversible first `SEND`. Enumerate every strict prefix (10 rows total including a failed-compensator control). Compare one monolithic fail-closed baseline with reverse-order saga compensation. A separate auditor uses an independently encoded schedule/classification table. No GUI, model, network, external effects, or task data.

**D.** Scoped PASS iff all 10 rows are present; both policies avoid `COMMITTED` for interrupted traces; saga resolves every non-empty fully compensatable prefix only when the compensation receipt succeeds; irreversible or failed-compensation prefixes remain unresolved; and applied-effect history is preserved. Any false compensation/commit or lost history is FAIL. Malformed/duplicate/missing rows are audit STOP.

**C.** The policies and action schedules are synthetic and hand-authored. Compensation success is represented by a trusted Boolean receipt; this experiment does not test whether a GUI compensator truly restores user intent or collateral invariants. The baseline is intentionally conservative.

**U.** No live application, task success, planner-boundary savings, latency benefit, crash consistency, or production transaction claim. This is distinct from the consumed 45-session GUI allocation and from T0–T3 toy probes. Results do not modify those records.

## Frozen provenance and execution

- Base: current-main `7fcf30f37e122bc3fce7ab893aebd9bfa4a864a8`.
- Candidate SHA-256: `e0f7a975c68549a8951b34aef5c36a354bb714fbe5a5d758cd358e49054d2082`.
- Independent auditor SHA-256: `fea9c504a22418a41641f1495a45328ccdd98ae2b4d892c4256029b986e7a238`.
- Planned command: `python3 research/analysis/saga_prefix_comparison_16_t4_v1/experiment.py`, followed only on successful exit by `python3 research/analysis/saga_prefix_comparison_16_t4_v1/audit.py`.
- Container status: not invoked. The shared OrbStack CPU lane is explicitly unassigned to this experiment in coordination Issue #5085; the only currently running container is unrelated and is left untouched. This host-only synthetic run is not a substitute for the separately consumed GUI allocation.
- One candidate invocation; no retry, tuning, replacement, or post-result source edits. Any source defect discovered after invocation is reported as a failed/STOP record, not silently repaired and rerun.
