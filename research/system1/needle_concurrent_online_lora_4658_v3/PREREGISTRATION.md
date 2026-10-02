# Needle LoRA/System-1 concurrent support-load experiment

Issue #4658. Allocation \`needle-concurrent-online-lora-4658-v3\`.

## H

Increasing the fixed support batch from #4653's 512 to 2048 rows/feedback arrival will create at least eight overlapping COW query intervals per seed during a 120-query, 60-Hz inference stream. Every COW result must still recompute exactly from its captured immutable adapter version, with p95 <=16.67 ms and no scheduled deadline misses.

## T

Fresh seeds 99771, 99883, 99991. Same CPU model family as #4631/#4653: 8 inputs, hidden 16 tanh, 4 outputs, rank-2 output LoRA; 12 sequential feedback arrivals, 16 AdamW steps/arrival, 2048 fixed support rows/arrival, 120 fixed queries paced at 60 Hz. One changed workload factor versus #4653: support batch 512→2048. Same seed-derived task rows/init/arrival order/labels/query across three arms.

Arms: (A) immutable inference-only baseline; (B) background candidate update with copy-on-write adapter version and atomic publish at feedback boundaries; (C) diagnostic shared-live mutation bracketed by odd/even generations, never eligible for PASS. Fixture-only outputs, authority=false, action emissions=0.

Corrected independent raw-only auditor retained from #4653 and extended to assert schema v3, batch=2048, query ordering and 12×16 training arrival/update ordering. Construction regression retains [8] query→exact [4] oracle logits parity and scalar rejection; all tests execute zero optimizer steps. Host wrapper default is construction-only; formal requires explicit \`--formal\`.

One local Docker orchestration: cached pinned image \`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e\`, Linux/amd64 CPU, 1 CPU/thread, 2 GiB, 64 PIDs, network none, read-only source/root, trainer and auditor in separate containers. No pulls, installs, GUI/user data, providers, live effects, retries, tuning, seed replacement, or runtime/action authority.

The formal host wrapper gives the trainer its own writable raw-output bind. The independent auditor runs afterward in a separate container with that raw bind mounted read-only and a distinct writable audit-output directory; it does not receive the trainer output mount as writable. Trainer and auditor stdout/stderr are retained by the host wrapper.

## D

\`PASS_COW_CONCURRENT_SYSTEM1_SCOPED\` only if 9/9 raw cells retained; trainer and independent auditor exit 0 with zero audit errors; all 360 COW logits \`torch.equal\` their immutable-version recomputation; base digest unchanged; and every COW seed has >=8 overlapping query intervals, inference p95 <=16.67 ms, and zero absolute scheduled 60-Hz deadline misses.

\`HOLD_NO_CONCURRENCY_PRESSURE\` if any seed has <8 overlaps. \`HOLD_LATENCY_BUDGET\` if integrity passes but a latency/deadline gate fails. \`FAIL_VERSION_INTEGRITY\` only for validated raw/model/version violation after construction regressions pass. Source/oracle/container/provenance defects are typed STOP, never a scientific model FAIL. Shared-live is diagnostic only. Exactly one formal run; no extension.

## C

Batch size changes optimization trajectory and compute duration, not contention alone. CPU scheduling and PyTorch behavior are host-specific; 2048 may still undershoot overlap or miss deadlines. COW may be stale while remaining internally consistent.

## U

Three seeds, one host/image, tiny synthetic task and 120 queries/arm. No real Astra feedback, task utility, GUI semantics, realistic large-model contention, cross-hardware/production guarantees, execution safety, or runtime promotion.
