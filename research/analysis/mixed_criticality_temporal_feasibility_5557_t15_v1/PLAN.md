# Issue #5557 T15 — temporal feasibility of mixed-criticality service contracts

## Status and lineage

This is a distinct finite experiment after T0–T14. Earlier work covered aggregate resource minima, explicit UNSAT classification, per-class and dependency-closure diagnosis, and freshness validity. T15 tests a temporal collision hidden by horizon-wide total capacity. No earlier allocation or raw result is edited or reused.

Issue preregistration comments: #5918821974 (H/T/D/C/U), #5918873465 (exact workload clarification), and #5919139236 (fresh T15-02 allocation and sole infrastructure correction). Frozen source main: `728d30cb2bf4e3b0a183a929258064d3ba823404`. T15-01 (run 36772395836) failed checkout with EACCES: candidate formal invocations 0; formal audit invocations 0. That immutable allocation is not rerun or edited. T15-02 (run 36772891046) successfully initialized the pinned container but stalled downloading the repository archive in `actions/checkout@v4` from 20:28:50Z until cancellation at 20:29:58Z; candidate formal invocations 0; auditor invocations 0; construction tests 0. No artifact files were produced. This is an infrastructure STOP, not a scientific result. The run log is retained in GitHub Actions and the stop is recorded in Issue comment #5919197649. Both allocations remain distinct and immutable.

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

Workflow: `.github/workflows/issue-5557-temporal-t15.yml`. Candidate command: `python -B experiment.py --output results/formal-02/raw.jsonl`. Audit command: `python -B audit.py results/formal-02/raw.jsonl --output results/formal-02/AUDIT.json`. Candidate and audit were not reached in T15-02; no result artifact exists. T15-01 showed runner EACCES with `--cap-drop=ALL` and `--security-opt=no-new-privileges`; T15-02 removed only those two options, keeping the digest-pinned image and CPU/memory/PID bounds, but checkout stalled downloading the archive. Neither allocation is rerun. No Docker daemon on the workstation is used.

## Preservation-run note and infrastructure successor boundary

The stop-recording commit `22d6859227d9009e814d8fd3a10b68bbef17fd08` triggered the same PR workflow because its path filter includes report updates. Preservation-only run 36773349770 was cancelled while checkout remained stalled; candidate, auditor, and construction-test steps were all skipped (0 invocations). This is not another allocation or a retry; see Issue comment #5919258256.

Repository precedent `.github/workflows/observation-recovery-contract-2452.yml` fetches exact PR-head files from `raw.githubusercontent.com` instead of using checkout/archive transport. A future allocation may preregister that transport, verify each fetched file against frozen SHA-256 values before tests or candidate execution, and enforce bounded network timeouts. This is only a candidate recovery path, not evidence that the transport will work or that the scientific hypothesis passes. T15-01 and T15-02 remain consumed STOP allocations.

## Terminal scope

Even a passing result is only a finite synthetic temporal-feasibility demonstration for these specific contracts. No task effect, live GUI, real-time OS, model, or production claim follows.
