# Corrected, higher-load concurrent Needle LoRA / System-1 experiment

Issue #4653. Allocation `needle-concurrent-online-lora-4653-v2`.

## H

At a fixed 60 Hz proposal schedule and fixed increased support batch, background candidate rank-2 LoRA updates can coexist with inference when each feedback-batch result is copy-on-write published as an immutable version. Every COW proposal must recompute exactly from its captured version and meet the frozen 16.67 ms deadline gate. Shared-live is a diagnostic-only unsafe comparison.

## T

Seeds 99119, 99221, 99331. Same fixed CPU model family as #4631: 8 inputs, hidden 16 tanh, 4 outputs, rank-2 output LoRA. Each seed/arm uses 12 sequential feedback arrivals; 16 AdamW steps per arrival; batch of 512 fixed support rows per arrival; 120 precomputed query rows paced at 60 Hz. The fourfold batch increase over #4631 is fixed before execution to raise the frequency/duration of trainer-inference overlap, based only on its raw timing diagnostics; it is not a post-result adjustment.

Arms: (A) inference-only immutable baseline; (B) background COW candidate updates with an immutable adapter snapshot and lock-protected pointer publication only after each feedback batch; (C) shared-live tensor publication after each optimizer update, bracketed by an odd/even generation. Same seed task, rows, initialization and update schedule across arms. All outputs are fixture-only; authority false; action emissions zero.

The independent auditor does not import the trainer. Construction tests explicitly prove a single query vector `[8]` produces exactly four logits, equals the trainer's forward result, and that scalar/wrong-shape logits are rejected. They also test snapshot digests, atomic version publication, unknown versions, and generation invalidity without constructing an optimizer. The host wrapper is safe-by-default: it executes construction only unless explicitly invoked with `--formal`.

One local Docker orchestration after all source/freeze bytes are published/read back: one trainer container and one separate auditor container, exact cached pinned image from #3890/#4631, Linux/amd64 CPU, one Torch intra/inter-op thread, network none, read-only source/root, bounded resources. No retries, tuning, seed replacement, pulls, installs, GUI/provider/user data, live effects, or action/runtime authority.

## D

`PASS_COW_CONCURRENT_SYSTEM1_SCOPED` only with 9/9 cells retained; all sources and snapshots hash-valid; independent raw-only audit zero errors; exact `torch.equal` recomputation for every COW proposal; unchanged immutable base; all COW cells have at least 8 query intervals overlapping trainer intervals; each COW seed p95 <=16.67ms and zero 60 Hz deadline misses.

Use `HOLD_NO_CONCURRENCY_PRESSURE` if a COW seed overlaps fewer than 8 query intervals. Use `HOLD_LATENCY_BUDGET` for cleanly audited p95/deadline misses. Use `FAIL_VERSION_INTEGRITY` only for a validated runtime/raw mismatch after the vector-shape regression tests pass. Auditor/schema/environment failure is STOP, never a model verdict. Shared-live remains diagnostic and cannot satisfy PASS. Report all seed/arm metrics; no retry, seed exclusion or post-result extension.

## C

The increased batch changes gradient workload and contention together relative to #4631. One small CPU model and local scheduler may not predict production-scale interference. A COW proposal may be stale but internally consistent until publication. Timing is host/image-specific.

## U

Synthetic support/labels, tiny network, three seeds, one local host/image and 120 queries/arm. No Astra feedback, real task success, GUI semantics, large-model contention, cross-hardware/production latency, action safety, or runtime promotion. Accuracy is descriptive and does not inherit another Issue's result.
