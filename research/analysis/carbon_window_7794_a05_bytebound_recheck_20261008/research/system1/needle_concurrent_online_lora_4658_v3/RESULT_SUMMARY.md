# Issue #4658 — concurrent online Needle LoRA/System-1

**Disposition: `HOLD_LATENCY_BUDGET`.** The sole frozen CPU Docker run and independent raw-only audit completed successfully with zero audit errors. All COW seeds met the preregistered overlap and inference-duration p95 gates, but seed 99771 missed three absolute scheduled 60-Hz deadlines; no candidate qualifies.

## Frozen execution

- Allocation `needle-concurrent-online-lora-4658-v3`; source commit `459bd5304c0cafa4ca1f4e94986568d9cb17f19a`; freeze SHA-256 `4aca60ffb00fb35b9c64edc04982051d09054ae34fb635ca9a70198f6c53553d`.
- Docker 29.8.0, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU, Python 3.12.14, PyTorch 2.5.1+cpu, one thread, network none, read-only source/root, 1 CPU / 2 GiB / 64 PIDs.
- Frozen construction suite 9/9; zero optimizer steps. One trainer container exit 0: nine cells, 120 queries/cell, 192 AdamW updates per trained cell; no worker errors. Independent auditor ran in a second container with raw mounted read-only and separate writable audit output; exit 0, zero errors. No retry or re-execution. Optional NumPy-missing warning only; no installation.
- Authority=false and action emissions=0. Shared-live is diagnostic only. Formal runner was invoked directly via the two recorded Docker commands; the host `formal.py --formal` wrapper was not invoked.

## COW per-seed results

| Seed | Overlap queries / 120 | p50 (ms) | p95 (ms) | Absolute 60-Hz deadline misses | Stream accuracy (descriptive) |
|---:|---:|---:|---:|---:|---:|
| 99771 | 8 | 0.245799 | 0.710754 | 3 | 64.17% |
| 99883 | 9 | 0.256655 | 0.380752 | 0 | 78.33% |
| 99991 | 8 | 0.241936 | 0.341823 | 0 | 87.50% |

All 360 COW query outputs recomputed exactly (`torch.equal`) from their captured immutable adapter versions; base digest unchanged. The p95 limit (16.67 ms) passed in all seeds; the zero-missed-deadline gate failed for seed 99771. Accuracy is descriptive, not an adoption gate.

Shared-live generation instability counts were 2/1/0 across seeds. This diagnostic negative control is not an eligible design.

## Evidence and limits

`EVIDENCE_MANIFEST.json` records byte counts/SHA-256 for all nine raw cells and `AUDIT.json`. The trainer/auditor invocation, completion and console logs are also retained in this directory. The 16,671,866-byte evidence ZIP is retained locally at `work/needle-concurrent-online-lora-4658-v3-20260927-formal01/EVIDENCE_BUNDLE.zip`, SHA-256 `ae1c157871731805518a8e72e12d378dfbafb39db8890482f8094125acd7cd0f`; it is not in the GitHub commit.

This is a three-seed synthetic tiny CPU-model component on one host. It establishes no real Astra feedback, task utility, GUI semantics, realistic large-model interference, cross-hardware/production guarantee, action safety, or runtime promotion. Preserve this HOLD; further experiments require a fresh successor.
