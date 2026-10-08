# Formal result — Issue #4769 / allocation r0

**Decision: `HOLD_NO_CONCURRENCY_PRESSURE`.** One formal orchestration ran all
six paired cells and the independent auditor in separate offline Docker
containers. All 7 invocations exited 0; the auditor found 0 integrity errors.
The preregistered CPU2 concurrency gate failed: every 2-vCPU seed overlapped
training in only 4/120 query intervals (gate: at least 8). CPU2 p95 latency was
within 16.67 ms for all seeds, but scheduled deadline misses were 2, 1, and 1,
so the independent latency/deadline gate also did not pass. The predeclared
decision precedence returns HOLD_NO_CONCURRENCY_PRESSURE when the overlap gate
fails; no pass is claimed.

| Seed | Arm | Training/query overlaps | Missed deadlines | p50 ms | p95 ms |
|---:|---|---:|---:|---:|---:|
| 9765101 | COW_CPU1 (1 vCPU) | 4/120 | 3 | 0.242424 | 0.668851 |
| 9765101 | COW_CPU2 (2 vCPU) | 4/120 | 2 | 0.258271 | 2.891809 |
| 9765203 | COW_CPU1 (1 vCPU) | 5/120 | 5 | 0.245803 | 1.913581 |
| 9765203 | COW_CPU2 (2 vCPU) | 4/120 | 1 | 0.249354 | 1.906736 |
| 9765307 | COW_CPU1 (1 vCPU) | 4/120 | 2 | 0.251514 | 1.944889 |
| 9765307 | COW_CPU2 (2 vCPU) | 4/120 | 1 | 0.243090 | 2.779017 |

## Frozen execution identity

- Issue: [#4769](https://github.com/Unjuno/agent-interface/issues/4769)
- Branch: `research/needle-cow-cpu-parallel-4769-v1-20260927`
- Additive research path: `research/system1/needle_cow_two_cpu_online_lora_v1/`
- GitHub-readback freeze: `FREEZE.json`; source SHA-256s and eight Git blob
  identities were checked before formal execution.
- Main at freeze: `eb9e74925b5d1d274f76cb3cbdd9071b67cbe1fe`; the original
  branch base `c193b77ddf84bb77fbaa480307c4b23600feedb1` is its ancestor.
- Docker client/server 29.8.0; host Windows 10, 20 logical CPUs; exact cached
  image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`
  (`linux/amd64`).
- Each trainer used `--network none`, `--read-only`, `--pull=never`, 2 GiB,
  64 PIDs, bounded tmpfs, and its assigned 1/2 CPU quota. Query period was
  16,666,667 ns; each cell ran 12 arrivals × 16 AdamW steps and 120 queries.
- Six exact-seed raw cells retained (6,675,300 bytes total); each has 192
  updates and 120 queries. Independent raw-only replay verified all six cells,
  all COW version snapshots, every proposal logit, and unchanged base weights.
  No action authority or action emissions were present.
- Full command vectors, timings, exit statuses, stdout/stderr digests and arm
  order are in `FORMAL_INVOCATION.json`; per-cell raw, audit and captured logs
  are retained under `outputs/needle-cow-two-cpu-4769-v1-formal/` locally and
  are preserved in this research subtree's `formal/r0/` evidence directory.

## Preregistered scope and interpretation

The treatment changes only Docker CPU quota, with Torch intra/inter-op thread
counts fixed at one. Fresh seeds are 9765101, 9765203, and 9765307. The
synthetic task, tiny model, one Windows/Docker Desktop host, and cached Linux
image do not establish real Astra feedback, useful skill learning, production
real-time performance, GUI semantics, action safety, cross-hardware behavior,
or runtime/product readiness. The observed low overlap means this workload
did not create enough concurrent pressure to answer whether extra CPU capacity
helps under a higher sustained training load. The old #4653 evidence and its
seed discrepancy remain unchanged.

## Preserved host-launch failure

An initial host wrapper launch explicitly requested `py -3.12`; the Windows
Python launcher returned exit 1 (`No suitable Python runtime found`) before
the wrapper started. No freeze was consumed, no formal-start marker or Docker
cell was created, and no output directory existed. The installed Python 3.11
runtime was then used for the single preregistered orchestration. This is a
host-launch/setup failure, not a formal cell retry or a scientific result.

## Git branch provenance event

After formal completion and before evidence upload, GitHub showed the original
allocated branch ref unexpectedly moved from executed/frozen commit
`4afc5b7b2ffbd964fbae710256d4b536a542a441` back to main
`eb9e74925b5d1d274f76cb3cbdd9071b67cbe1fe`. This was verified with GitHub MCP
branch lookup, ref lookup, and search; the commit object remained fetchable.
The worker did not force-update that ref. A recovery branch
`research/needle-cow-cpu-parallel-4769-evidence-v2-20260927` was created from
the retained executed commit to preserve its frozen source and append the
result/raw evidence. The ref drift is disclosed and does not alter the local
formal run or its raw files.

## H/T/D/C/U disposition

- **H:** Not supported by this allocation: the 2-vCPU arm failed the overlap
  threshold in all three seeds. No causal CPU-capacity conclusion under a
  sufficiently pressured workload is claimed.
- **T:** Matched synthetic online rank-2 LoRA; only Docker quota changed
  (1 vs 2 vCPU); three fresh paired seeds, six isolated trainer containers.
- **D:** Integrity passed (0 audit errors), but concurrency and deadline gates
  did not; retain the preregistered HOLD without tuning or rerunning these
  seeds.
- **C:** Docker quota is not core reservation; host scheduling, virtualization,
  thermal state and neighboring load remain confounders. Fixed single-thread
  Torch and alternating arm order constrain but do not remove them.
- **U:** Scoped only to this fixture workload, seeds, host and image; no runtime
  promotion, general Needle efficacy, live model fine-tuning, or role-network
  skill claim follows.
