# Issue #5189 — duplicate-seed STOP and retained non-adjudicative observation

**Allocation disposition: `STOP_DUPLICATE_FORMAL_SEED_COLLISION`.** This branch's frozen source commit was not the first use of formal seeds 484431/484432. A separate report on Issue #5184 records a Docker runner started at 2026-09-28 13:18 JST using those same seeds under source commit `2a96313df5edffb1f7d180bee6c142917ac79e37`; this branch's runner container was created at 2026-09-28 04:24:55 UTC (13:24:55 JST), after that reported start. Issue #5189 was subsequently closed as a duplicate consumed allocation. Therefore this branch's run is retained as a **non-adjudicative duplicate-seed observation**, not a valid fresh formal allocation, independent replication, or scientific conclusion. Do not pool the runs or reuse the seeds. The earlier allocation-success/HOLD wording in this file's Git history is superseded by this provenance correction.

The Docker run and raw-only auditor described below did execute against this branch's frozen source, and the auditor validated this raw artifact. That proves artifact consistency only; it cannot restore seed novelty or allocation validity.

## Retained execution and evidence (not a valid allocation)

- Reported allocation ID `typed-mode-4844-successor-20260928-03`; training/heldout seeds 484431/484432; 2,000 balanced training rows and 4,800 heldout rows (960 in each of five blocks, 192 per mode/block). These seeds had already been reported consumed by the competing run.
- Source freeze commit `fcf06f1bf4ce85952658cf9f53e38899dfc51530`; exact source hashes/Git blobs and commands are in [FREEZE.json](FREEZE.json) and [PLAN.md](PLAN.md). Formal source copied byte-for-byte from that commit and rechecked before launch.
- Docker Desktop `desktop-linux`, Docker client/server 28.5.1; image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` (`linux/amd64`, Python 3.12.14). Runner and auditor each used network `none`, read-only root, read-only source, 1 CPU, 512 MiB, 32 PIDs, `no-new-privileges`, and bounded tmpfs `/tmp`. No other container was running at preflight or left running afterward.
- Runner container `e3b9b407bbbb71b7f70663417fab548d273db7f6906e4da85a76143efc93c4cf`, exit 0. Auditor container `48bd68fdee2e2276521212c522760c5eeccb8f7ed3a5238e859f64325d8a1626`, exit 0. Each was inspected and removed after exit. No runner/auditor retry.
- Raw result: 1,542,155 bytes, SHA-256 `74dfede0db4676fdaf0d6385c625c2c3731a75ffe8572d7f7a45dbc060e42a22`. Full raw rows, both logs, receipts, container IDs/inspect records and auditor receipt are retained under `formal/allocation-03/`.
- Runner stdout/stderr were combined by the frozen PowerShell `2>&1 | Tee-Object` command; the exact combined streams are retained as `runner.log` and `auditor.log`.

## Raw-derived metrics (exploratory observation only; not an allocation result)

Wrong emitted dispositions and safe-coverage rates (each block n=960):

| Block | Direct wrong | Typed wrong | Wrong reduction | Direct coverage | Typed coverage | Typed − direct coverage |
|---|---:|---:|---:|---:|---:|---:|
| SINGLE_MISSING | 47 | 53 | −12.8% | 29.896% | 75.208% | +45.312 pp |
| MULTI_MISSING | 36 | 69 | −91.7% | 27.396% | 67.604% | +40.208 pp |
| COMPOSITION_HOLDOUT | 215 | 169 | +21.4% | 73.854% | 66.771% | −7.083 pp |
| COMPLETE | 71 | 30 | +57.7% | 94.583% | 94.479% | −0.104 pp |
| NUISANCE_SHIFT | 108 | 119 | −10.2% | 67.083% | 71.979% | +4.896 pp |

If considered descriptively in isolation, the raw-derived metrics do not satisfy the frozen primary gate: SINGLE_MISSING and MULTI_MISSING have more wrong typed emissions, and COMPOSITION_HOLDOUT's 21.4% reduction accompanies a 7.083 pp coverage loss. Because the allocation is invalidated by the seed collision, do **not** assign the scientific disposition `HOLD_COVERAGE_TRADEOFF` to this allocation from those metrics.

The retained raw/audit pair reports all five noiseless full-observation prototypes correct and arm-equal; unknown and contradictory controls abstained in both arms; unsafe emissions were zero. Auditor receipt: `pass=true`, rows=4,800, errors empty, 16/16 corruption controls rejected. These validate this retained synthetic artifact only.

## Scope and limits

This duplicate run cannot support a fresh-seed replication claim or an independent estimate. Preserve it separately from the competing report on #5184; do not pool the two raw outputs. No real GUI diagnosis, cross-app transfer, runtime integration/authority, safety proof, model quality, task effect, latency/token efficiency, human tempo, or product claim follows. Earlier #4155/#4169/#4844/#4863/#5184/#5188 evidence and STOP records are unchanged.
