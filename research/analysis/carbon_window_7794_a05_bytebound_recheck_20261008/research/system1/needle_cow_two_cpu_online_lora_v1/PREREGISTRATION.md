# Issue #4769 — 2-vCPU COW Needle LoRA/System-1 study

Allocation `needle-cow-two-cpu-online-lora-4769-v1`, branch
`research/needle-cow-cpu-parallel-4769-v1-20260927`, additive path
`research/system1/needle_cow_two_cpu_online_lora_v1/`.

## H — hypothesis

Against the matched 1-vCPU reference, a 2-vCPU quota on the same fixed
single-threaded online rank-2 LoRA workload will permit meaningful COW
trainer/inference overlap (at least 8 of 120 queries per seed), while meeting
the 60-Hz p95/deadline gates and exact immutable-version integrity checks.

## T — treatment

Fresh seeds are 9765101, 9765203, and 9765307. For each seed, run
`COW_CPU1` and `COW_CPU2` with the same generator, base, support tensors,
initial adapter, feedback sequence, optimizer, queries and absolute schedule.
The only treatment is the Docker CPU quota, 1 versus 2 vCPUs. Each cell performs
12 feedback arrivals, 16 AdamW updates per arrival on a fixed 512-row batch,
and 120 inference queries at 60 Hz. Torch intra/inter-op threads remain 1.

The pair order alternates by seed parity. Each cell runs in a separate,
network-disabled container on cached `needle-pilot05:local` image ID
`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`,
Linux/amd64, read-only root and source, 2 GiB, 64 PIDs, bounded tmpfs. Every
query records schedule/deadline, start/end, latency, exact captured version,
inputs, logits and training-interval overlap. Every feedback publication is
immutable and content-digested. All outputs are fixture-only, with authority
false and zero action emissions.

The separate raw-only auditor independently regenerates all data and initial
weights, replays every optimizer update, verifies exact seed identity, version
snapshots and package digests, recomputes each proposal with `torch.equal`,
checks overlap/deadline accounting, and compares the matched trained snapshots.
Construction tests take zero optimizer steps and cover quota bindings, oracle
shape, seed identity, timing boundaries, snapshot publication, and preflight.

One formal orchestration only. No retries, tuning, seed replacement, package
installation, model pull, GUI/user data, external provider, live effect,
authority, or product/runtime promotion. If any frozen source/seed/image/raw
identity fails, report STOP. The previous #4653 allocation is preserved
unchanged; its issue/freeze seeds (99119/99221/99331) disagree with its raw
audit seed IDs (88117/88229/88301). None are reused here.

## D — decision

- `PASS_COW_TWO_CPU_SYSTEM1_SCOPED`: all six raw cells retained; zero audit
  errors; every 2-vCPU seed has >=8 overlap queries, inference p95 <=16.67 ms,
  and zero scheduled deadline misses; all COW proposals recompute exactly and
  the immutable base is unchanged.
- `HOLD_NO_CONCURRENCY_PRESSURE`: any 2-vCPU seed has fewer than 8 overlap
  queries.
- `HOLD_LATENCY_BUDGET`: integrity passes but a 2-vCPU seed misses a latency
  or deadline gate.
- `STOP_SEED_OR_VERSION_PROVENANCE`: any source, image, seed, snapshot, or
  independent-oracle identity is not verifiable.

## C — alternatives / confounders

The 1-vCPU reference may already satisfy the gates; Docker quota does not
reserve host cores. Shared-host agent/container load, virtualization, thermal
state and scheduler variation affect timing. Alternating pair order and
per-cell host/container receipts limit but cannot eliminate these confounders.

## U — scope

Three fresh synthetic seeds, one Windows/Docker Desktop host, one Linux/amd64
image and one tiny model. This tests CPU-capacity effects for concurrent
online-LoRA fixture inference only; it does not establish Astra feedback,
production real-time performance, broad adaptation quality, GUI success,
cross-hardware behavior, action safety or runtime readiness.
