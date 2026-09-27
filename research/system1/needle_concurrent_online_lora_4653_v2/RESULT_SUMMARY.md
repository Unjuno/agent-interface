# Issue #4653 — concurrent online Needle LoRA/System-1 inference

**Disposition: `HOLD_NO_CONCURRENCY_PRESSURE`.** The corrected independent raw-only audit completed with zero errors and exactly recomputed every COW proposal from its captured version. However, despite the fixed fourfold support-batch increase, each seed had only five COW query intervals overlapping trainer intervals (gate: at least eight). In addition, seed 99119 had two 60 Hz deadline misses. Per-query p95 latency was below 16.67 ms in all three seeds, but the frozen no-missed-deadline gate did not pass. No candidate is qualified.

## Execution

- One explicit host invocation with `--formal`; construction-only default was exercised separately after freeze. One trainer container and one independent auditor container; retries/tuning/seed replacement: 0.
- Frozen source SHA-256: `071b2bb7327c846a1b37164df1bb721d86115a18bd40c24e0bb87d0ee601f5d2`.
- Cached Docker image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; Docker 29.8.0, Linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, one CPU / one intra-op and inter-op thread, no network, read-only source/root, 2 GiB / 64 PIDs.
- Frozen Docker construction suite: 8/8, including explicit one-query `[8]` → four-logit oracle parity and scalar rejection; no optimizer steps in tests.
- Seeds 99119, 99221, 99331; all nine seed/arm cells retained; 120 queries per cell; 192 AdamW adapter steps in each trained cell; no trainer worker errors; no action authority/emissions.
- Independent auditor exit 0; zero errors. All 360 COW query outputs exactly match the captured immutable adapter-version recomputation, and base digests remain unchanged. Shared-live is diagnostic only.

## COW measurements

| Seed | Overlap queries / 120 | p50 inference (ms) | p95 inference (ms) | 60 Hz deadline misses | Stream accuracy (descriptive) |
|---:|---:|---:|---:|---:|---:|
| 99119 | 5 | 0.240693 | 0.668744 | 2 | 55.83% |
| 99221 | 5 | 0.240953 | 0.345447 | 0 | 80.00% |
| 99331 | 5 | 0.199260 | 0.275208 | 0 | 79.17% |

Overlap remained below eight in all seeds. The first seed also missed the absolute scheduled completion deadline twice despite low inference-duration p95; scheduled lateness and query execution duration are distinct measurements. Stream accuracy is over the 120 evolving-version queries and is descriptive, not a separate skill-quality pass.

The SHARED_LIVE arm recorded generation instability on one query for seed 99119 and none for the other two seeds. It remains an intentionally diagnostic, non-authoritative arm; this does not establish a COW-versus-shared causal safety claim.

## Scope / next step

This is clean, scoped evidence that the *tested workload* did not sustain the preregistered concurrency pressure and had two deadline misses in one seed. It does not establish production real-time adaptation or action authority. Preserve this allocation unchanged. Any further pressure-scale measurement needs a new successor with a single fixed workload increase, fresh seeds, and the corrected oracle regression test; no extension or rerun of #4653 is permitted.
