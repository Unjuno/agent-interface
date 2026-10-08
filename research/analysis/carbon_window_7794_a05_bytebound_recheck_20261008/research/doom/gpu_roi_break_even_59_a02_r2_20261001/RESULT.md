# #59 GPU ROI transfer-cost diagnostic — A02 result

**Result:** `PASS_RAW_AUDIT`; `GPU_SPEEDUP_OBSERVED_IN_SCOPED_CELLS`.

The sole candidate completed on the local RTX 3080 with exit code 0. Exact CPU/CUDA changed-pixel counts matched in all 12 cells and all 21 timed repeats per cell. The independent raw-only NumPy auditor completed once with exit 0, 12/12 cells, and zero errors. CUDA median latency was lower in 10/12 cells. This is synthetic compute evidence only, not real-frame or live-control evidence.

## H / T / D / C / U

- **H:** For the frozen one-way changed-pixel metric, CUDA including transfers and synchronization exactly matches CPU counts; latency may cross over at larger ROI/batch sizes.
- **T:** One seeded deterministic uint8 RGB sweep, seed 59020261002; dimensions 95×50, 320×200, 640×400, 1280×800; batches 1, 4, 16; 3 warmups plus 21 alternating-order timed repeats per arm/cell. Pixel change: maximum absolute RGB-channel delta >32. Frame invalidation: changed pixels ≥100. CUDA timing includes H2D, conversion, delta/reduction, synchronization and D2H. Fixture generation is outside the timed region.
- **D:** All count vectors matched; independent audit PASS. Ten cells had CUDA median < CPU median. The two exceptions were 95×50 batches 1 and 4. Therefore this is a scoped measured crossover, not a general GPU-benefit claim.
- **C:** Windows 10 build 26200 host; Python 3.11.9, NumPy 2.4.6, PyTorch 2.5.1+cu121/CUDA 12.1, NVIDIA GeForce RTX 3080 Laptop GPU. Device clocks/load and allocation/transfer overhead are host-specific.
- **U:** Random synthetic RGB only. This does not establish real UI ROI distributions, visual/HUD recognition, useful feedback, threat detection, action validity, task success, survival, MAP01 exit, safety, or product value. No model/game/GUI/input/network/Docker was used. Allocation A01's raw-unavailable STOP is unchanged; the A02 R1 stale-base prelaunch refreeze was candidate=0 and is preserved separately.

## Exact cell summaries

Times are milliseconds. Ratio is CUDA median / CPU median; values below 1 favor CUDA for that synthetic cell.

| ROI | Batch | CPU median | CUDA median | Ratio | CPU p95 | CUDA p95 |
|---|---:|---:|---:|---:|---:|---:|
| 95×50 | 1 | 0.1072 | 0.1757 | 1.639 | 0.1137 | 0.2111 |
| 95×50 | 4 | 0.3887 | 0.4416 | 1.136 | 0.4018 | 0.5566 |
| 95×50 | 16 | 1.4738 | 0.5454 | 0.370 | 1.5248 | 0.6972 |
| 320×200 | 1 | 1.2474 | 0.5495 | 0.441 | 1.2843 | 0.6541 |
| 320×200 | 4 | 5.8771 | 1.0977 | 0.187 | 6.1597 | 1.4257 |
| 320×200 | 16 | 23.2670 | 2.3986 | 0.103 | 23.7896 | 3.2581 |
| 640×400 | 1 | 5.8378 | 1.0774 | 0.185 | 6.1073 | 1.5093 |
| 640×400 | 4 | 23.3514 | 2.7710 | 0.119 | 24.1688 | 3.2123 |
| 640×400 | 16 | 94.9032 | 8.9394 | 0.094 | 101.1393 | 11.4438 |
| 1280×800 | 1 | 23.4244 | 2.7963 | 0.119 | 24.5248 | 2.9951 |
| 1280×800 | 4 | 92.5222 | 9.0005 | 0.097 | 94.4962 | 10.9445 |
| 1280×800 | 16 | 400.7296 | 38.9950 | 0.097 | 489.2706 | 104.5928 |

The small single-frame ROI result matters for a high-frequency feedback path: it was slower on CUDA here. Most larger cells favored CUDA, but synthetic random pixels and batching do not reproduce real application crops or observation traffic.

## Provenance and execution

- Allocation: `MAP01-ROI-BREAK-EVEN-59-GPU-20261001-02`.
- Source main: `45395880f873f1592bc188a37471d8380535e1ec`.
- Branch/path: `research/doom-gpu-roi-break-even-59-a02-r2-20261001` / `research/doom/gpu_roi_break_even_59_a02_r2_20261001/`.
- Final gate at 2026-10-01T06:13:30.4196653Z: `PREFLIGHT_OK`, 0%, 0 MiB, zero compute-app rows. The user-authorized RTX 3080 reservation was released after candidate and audit completion.
- Candidate command: `pwsh -NoLogo -NoProfile -File .\launch.ps1`; candidate child exit 0; candidate invocations 1; retries 0.
- Raw audit command: `py -3.11 -B audit.py .\raw\candidate.json`; audit exit 0; auditor invocations 1.
- Raw candidate: 39,376 bytes; SHA-256 `28855f08aa511668e0f27407015b6711392a1a1699ddc7ddbd324515ea4fbfbd`.
- Runner SHA-256 `59a977905af3c20cef5bde96ec4cd54f0084d6e98e497f88d6b5430839b46433`; auditor SHA-256 `ae5936de4bf7347cea667fc681ead762c29f60e8408ec9f309d385594e536524`.

Full source pins and raw artifacts are colocated under this package. The result is not a retry of A01 and does not satisfy Issue #59's live threat-exposure exit condition.
