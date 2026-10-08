# Formal result — online LoRA correction cadence v1

Issue: [#4888](https://github.com/Unjuno/agent-interface/issues/4888)  
Allocation: `needle-online-correction-cadence-20260927-v1`  
Freeze SHA-256: `64d6ed5165a064f9268deee81784ed7a1ec8e76328e8e61f229d006b953c17c9`

## H / T / D / C / U

- **H:** Immediate single-row rank-2 LoRA updates acquire the opposing B task; true microbatch-2 might retain the original A task better at equal optimizer-step count.
- **T:** One formal Docker orchestration, seeds 734211/734311/734411, 128 adapter optimizer steps per arm per seed, exact cached image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (linux/amd64), CPU-only, no network/pull, read-only source/root, 1 CPU, 2 GiB, 64 PIDs. Run completed 2026-09-27 13:37:15–13:37:19 UTC; independent audit ran separately and completed without errors.
- **D:** `PASS_AUDIT`, 0 integrity/replay/provenance errors, 96 arrival checkpoints. Scientific decision: **`FAIL_SCHEDULE_QUALITY_OR_RETENTION`**. Every seed and both schedules ended held-out A=0.000 and B=1.000; mean final-A gain from microbatch-2 was 0.000 (required >=0.05). Both schedules acquired B, but both forgot A. The update-duration gate passed: maximum individual optimizer step was 3.245 ms (all <60 ms). Microbatch-2 delayed the A collapse by roughly one arrival in one seed, but not the other two; this is descriptive only, not a retained-quality win.
- **C:** Exactly one formal runner orchestration, exit 0, no retries; one separate raw-only auditor container, exit 0. Full raw JSON SHA-256 `cb71d4cd03f6073bac4492ca8f6711e7be9b2bd2e490a90dae546d1a06b784db`, 747,656 bytes. Gzip transport copy SHA-256 `028ffac22807d137cdf6e40dd2d56fa8cd2a004a2e16738f888d95aaee752c09`, 263,279 bytes; decompression reproduces the exact raw bytes. Invocation and audit receipts bind exact stdout/stderr/raw hashes. Stderr contains only the image's NumPy initialization warning; no experiment code depends on NumPy.
- **U:** Synthetic eight-feature binary-factor task, three seeds, one cached CPU image/host. It does not establish live Needle skill learning, real-time feedback latency, a role-network skill, general LoRA behavior, or production value. No runtime/product code changed and no adaptation was promoted.

## Per-seed terminal metrics

| Seed | SINGLE final A/B | MICROBatch2 final A/B | max step SINGLE / MICROBatch2 |
|---|---|---|---|
| 734211 | 0.000 / 1.000 | 0.000 / 1.000 | 3.245 / 1.170 ms |
| 734311 | 0.000 / 1.000 | 0.000 / 1.000 | 0.391 / 0.291 ms |
| 734411 | 0.000 / 1.000 | 0.000 / 1.000 | 0.385 / 0.781 ms |

Exact raw evidence and receipts are preserved alongside this report. The failed quality outcome is retained as-is; no tuning or replacement run is authorized by this allocation.
