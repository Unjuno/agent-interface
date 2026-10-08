# Issue #4821 — formal GPU STOP

## Disposition

**STOP `REPEATED_QUERY_NONDETERMINISM` at `repeat_queries`.** This is the single frozen formal invocation. Do not retry or repair this allocation. No complete `RESULT.json` was produced, so no inference-runtime PASS/FAIL decision is available.

## Observed run

- One runner container, one exact pinned CUDA image (`sha256:01ea4e60b03e8a7d48644d0dce596bd2e42ab3815fdc52b0c7a6d4cbcf757dac`), RTX 3080 Laptop GPU, network `none`, read-only root, 1 CPU / 4 GiB / 128 PIDs.
- Model loaded once: 75,670,026 parameters (302,680,104 parameter bytes), resident on `cuda:0`; CUDA allocation 311,200,768 bytes. Optimizer-step calls: 0.
- 16 warmups and all 1,024 formal rows were recorded. Repeating the first 16 formal queries produced 12/16 rows exceeding the frozen maximum absolute probability difference of 1e-6; maximum observed absolute difference was 0.018063053488731384.
- Formal warm query latency was around 40–43 ms after the first call, but the integrity gate stopped the allocation before a valid complete result; this latency is descriptive only and cannot satisfy the preregistered decision.
- STOP raw record contains 1,056 partial query records. The separate frozen STOP auditor passed with zero errors. Runner exit 1; STOP audit exit 0. GPU returned to 0 MiB after completion.

## Collision / execution provenance

The fresh preflight recorded RTX 3080 idle and only the existing caller-owned Ollama container running. Concurrent #4829's GPU trainer and auditor were terminal; its remaining work was GitHub evidence upload. No other live GPU allocation remained. The collision record was generated immediately before launcher preflight. Its ISO timestamp includes the local UTC+09 offset because PowerShell ConvertFrom-Json normalizes Z timestamps to local time in the frozen launcher; that explicit offset represents the same instant and passed the launcher freshness check.

## Cause boundary

This demonstrates output nondeterminism under repeated predictions from the frozen Mitra API/runtime path, despite zero optimizer steps. It does not identify whether the variation comes from the API, stochastic inference behavior, or an internal implementation detail. It cannot establish accuracy, calibration, generalization, or product benefit. Allocation consumed; no retry or post-result source modification.