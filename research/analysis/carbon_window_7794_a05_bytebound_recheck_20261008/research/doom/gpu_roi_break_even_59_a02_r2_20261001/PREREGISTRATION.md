# #59 GPU ROI transfer-cost successor A02 refreeze

Allocation: MAP01-ROI-BREAK-EVEN-59-GPU-20261001-02
Owner/task: Unjuno / Codex task 01a0b98f-d6dd-79a0-9f0e-74c29b91a1d4
Branch: research/doom-gpu-roi-break-even-59-a02-r2-20261001
Additive path: research/doom/gpu_roi_break_even_59_a02_r2_20261001/
Frozen source main: 45395880f873f1592bc188a37471d8380535e1ec
Exact owner-authorized RTX 3080 remainder window: 2026-10-01 06:11–06:20 UTC; #5085 comment #5925778576.

## H / T / D / C / U

- H: For the frozen one-way changed-pixel metric, CUDA including host↔device transfer and synchronization returns exactly the CPU count vector for each deterministic RGB fixture. End-to-end latency may cross over at larger ROI/batch sizes; speedup is observed only in cells whose CUDA median is lower.
- T: One host-only candidate on the Windows RTX 3080. Deterministic seeded uint8 RGB pairs; ROI dimensions 95×50, 320×200, 640×400, 1280×800 and batch sizes 1, 4, 16. A pixel changes iff max absolute RGB-channel delta >32; a frame is invalidated iff changed pixels ≥100. Three warmups and 21 alternating-order timed repeats per CPU/CUDA arm/cell; GPU time includes both transfers, cast/delta/reduction, synchronization and result copy. Inputs are generated outside timing. launch.ps1 enforces the fail-closed GPU gate and run_capture.py durably publishes complete stdout bytes to a fresh raw path and records stderr, exit code and digest. One separate NumPy raw-only audit follows only a durably published completed candidate, including a completed parity-failure raw.
- D: FAIL_GPU_CPU_PARITY if any of the 12×21 count vectors differs from the independent NumPy oracle. With parity intact, report every median/p95 and exact break-even cell; GPU_SPEEDUP_OBSERVED_IN_SCOPED_CELLS only if at least one frozen cell has CUDA median < CPU median, otherwise GPU_SPEEDUP_NOT_ESTABLISHED. PASS_RAW_AUDIT is necessary for a scoped conclusion. Missing/ambiguous resource data, changed source, unavailable CUDA, invalid output, or audit mismatch is STOP/HOLD; never retry. A completed non-parity child exit (1) is auditable only when full JSON is durably published and status agrees with parity.
- C: Windows host; Python 3.11.9, NumPy 2.4.6, PyTorch 2.5.1+cu121/CUDA 12.1, NVIDIA GeForce RTX 3080 Laptop GPU. Synthetic random RGB input; transfer/tensor allocation, OS/GPU load, clock and thermal state affect timing.
- U: Deterministic synthetic computation diagnostic only. It does not establish that real UI frames have these ROI distributions, that HUD/health is recognized, that GPU speeds up live feedback, or threat detection, action validity, task success, survival, MAP01 exit, safety, or product benefit. Preserve A01 STOP_PROTOCOL_DEVIATION_RAW_UNAVAILABLE unchanged. This is still candidate 0 of the unconsumed A02 allocation, now refrozen on a new exact-main branch/path after the stale-base gate; not a retry/reconstruction of A01 output.

## Commands and start gates

Before launch, independently verify main still equals the frozen SHA, confirm #5085 queue and process owners, and check nvidia-smi plus compute-app inventory. Any main advance or active/unparseable GPU process is a pre-candidate STOP and requires re-arbitration.

- Candidate: pwsh -NoLogo -NoProfile -File .\launch.ps1
- Raw-only CPU audit, only if launch returns 0 and candidate.json plus publication_receipt.json exist: py -3.11 -B audit.py .\raw\candidate.json

No Docker/OrbStack, model, game, GUI, OS input, network, or task effect.
