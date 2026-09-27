# Needle concurrent online LoRA / System-1 experiment

Issue #4631. Allocation `needle-concurrent-online-lora-4631-v1`.

## H

A rank-2 candidate LoRA trained in a background worker can coexist with a 60 Hz local inference stream when updates are copy-on-write and active versions are atomically published. Every proposal should be attributable to exactly one immutable active version, with no 16.67 ms deadline misses. The shared-live arm is a diagnostic negative control only.

## T

Three fixed seeds: 88117, 88229, 88301. Tiny fixed CPU model: 8 inputs, hidden width 16, four outputs, rank-2 output LoRA. For each seed: 12 fixed feedback arrivals, 16 AdamW steps per arrival, support batch 128 (same support batch repeated within its arrival), and 120 fixed held-out inference queries on a 60 Hz schedule. Same base, labels, query rows, initialization, and optimizer schedule across all arms.

Arms: (A) immutable inference-only baseline; (B) background candidate updates, immutable copy-on-write adapter snapshot after each feedback batch, lock-protected atomic version pointer; (C) diagnostic shared-live in-place tensor publication after each optimizer update, bracketed by an odd/even generation counter. C has no execution authority and is never considered a candidate architecture.

Construction-only host/container tests do not instantiate an optimizer or train. One frozen Docker orchestration runs the trainer once and the independent auditor once in distinct network-disabled containers. No retry, tuning, seed substitution, image pull/install, GUI, user data, provider, live effect, or action authority.

## D

Scoped PASS requires: zero independent-audit errors; exact COW proposal recomputation from the recorded immutable version; unchanged base; valid version/generation transitions; at least 8 query intervals overlapping training per seed in the COW arm; and zero COW 60 Hz deadline misses with each seed p95 inference latency <=16.67 ms. Any integrity discrepancy is `FAIL_VERSION_INTEGRITY`; quality/latency-gate miss with clean evidence is `HOLD_LATENCY_BUDGET`; insufficient overlap is `HOLD_NO_CONCURRENCY_PRESSURE`. Shared-live overlap and latency are descriptive only. No retry or post-result extension.

## C

Host scheduling, Python and CPU contention affect timing. Copy-on-write avoids in-place mutation of the active adapter but may serve an older, internally consistent version until publication. Shared-live intentionally permits readers to observe a write in progress, but remains fixture-only. Training and inference are both synthetic CPU workloads.

## U

One host, pinned image, small synthetic network, three seeds, 120 queries/seed/arm. No Astra feedback, real task quality, GUI semantics, large-model contention, cross-hardware latency, safety or runtime promotion claim.
