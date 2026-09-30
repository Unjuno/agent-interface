# Issue #5557 T15 — temporal feasibility of mixed-criticality service contracts

## Status and lineage

This is a distinct finite experiment after T0–T14. Earlier work covered aggregate resource minima, explicit UNSAT classification, per-class and dependency-closure diagnosis, and freshness validity. T15 tests a temporal collision hidden by horizon-wide total capacity. No earlier allocation or raw result is edited or reused.

Issue preregistration comments: #5918821974 (H/T/D/C/U) and #5918873465 (exact workload clarification). Frozen source main: `728d30cb2bf4e3b0a183a929258064d3ba823404`. Candidate formal invocations: 0; formal audit invocations: 0 at freeze.

## Frozen design

- Horizon ticks: 0, 1, 2, 3.
- Enumerate all 16 binary HI-arrival vectors in both capacity regimes (32 rows).
- Each active HI arrival needs 2 units at its release-tick deadline.
- RECOVERY_OBSERVER needs 1 unit at each tick (`max_gap=1`, including the initial tick-0 obligation).
- LO_PLANNER requires at least 1 unit over the horizon. Remaining units are BACKGROUND.
- Regime A capacity is 2 units/tick. Aggregate-only checks `2*HI_count + 4 + 1 <= 8`, which marks zero- and one-HI rows feasible; a one-HI row nevertheless has a same-tick 3-unit HI+observer demand and is temporally UNSAT.
- Regime B capacity is 3 units/tick. HI+observer can coexist; up to three HI arrivals leave enough residual for the planner minimum; four do not.
- Compare horizon-total-only feasibility, HI-priority greedy service, and fail-closed temporal contract scheduling.
- Candidate writes one JSONL raw. Independent auditor reconstructs all rows without importing candidate and rejects three in-memory corruption controls.

## H/T/D/C/U

- **H:** Per-tick HI deadline and observer max-gap enforcement exposes temporal infeasibility despite aggregate headroom, while feasible traces preserve the LO minimum.
- **T:** One digest-pinned GitHub Actions container job on `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; no model, GUI, network service, GPU, or task input. Run independent construction tests first, invoke candidate once, then raw-only audit once. Keep the generated files as workflow artifact, then commit those exact bytes into this additive path. A result-recording follow-up must not invoke candidate again.
- **D:** `PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED` only when 32 unique rows match independent reconstruction; all SAT schedules meet each tick's HI and observer contracts and the LO minimum; temporal conflicts are explicit UNSAT with no dispatch; the capacity-3/three-HI feasible control remains SAT; and all three non-identity mutations are rejected. Any hard-contract violation is FAIL; provenance/container/audit failure is STOP.
- **C:** Aggregate totals may suffice where service is freely fungible; HI-priority plus explicit fail-closed may be adequate. Compare baseline outputs directly.
- **U:** Authored binary arrivals, one resource, four ticks, and deterministic service do not establish live workload distributions, semantic observation utility, general schedulability, production safety, or product benefit.

## Exact execution protocol

Workflow: `.github/workflows/issue-5557-temporal-t15.yml`. Candidate command: `python -B experiment.py --output results/formal-01/raw.jsonl`. Audit command: `python -B audit.py results/formal-01/raw.jsonl --output results/formal-01/AUDIT.json`. Candidate and audit each run once, sequentially, only when the branch head does not carry the `[t15-results-recorded]` marker. Results are uploaded as Actions artifact; after download, their bytes are committed unchanged. No Docker daemon on the workstation is used.

## Terminal scope

Even a passing result is only a finite synthetic temporal-feasibility demonstration for these specific contracts. No task effect, live GUI, real-time OS, model, or production claim follows.
