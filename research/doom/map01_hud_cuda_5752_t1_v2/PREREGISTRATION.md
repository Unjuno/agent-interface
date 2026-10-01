# Issue #5752 GPU HUD reader spike — preregistration

Allocation GPU-HUD-CUDA-5752-20261001-02; successor to closed Issue #503; supports measurement readiness under #59 only.
Base main: 8827fad422b225bddd9b1c6d34bfa68ca19265c5.
Branch: research/gpu-hud-cuda-5752-20261001-02.
Evidence path: research/doom/map01_hud_cuda_5752_t1_v2/.

## H / T / D / C / U

- **H:** A PyTorch CUDA implementation of the existing WAD-template HUD reader exactly matches the CPU health/ammo reader on all 23 selected screenshots and reduces warm per-frame decode-plus-read p50 by at least 2×.
- **T:** Use 19 in-envelope observations from the four fixed #503 plans plus their four baseline frames. Inputs are selected from v38 map01-v38-integrated-threat-live-01 and v39 map01-v39-coast-liveness-live-01; dataset.json freezes per-frame source path, geometry, encoded-PNG SHA-256 and decoded-RGB SHA-256. The original report/events files remain SHA-bound. Freedoom 0.13.0 archive and WAD hashes are pinned. CPU reference is the unchanged hud_independent.py source from main. Run 30 alternating CPU/GPU per-frame pairs over the 23 frames; both paths include image decoding, CUDA includes host-to-device copy and explicit synchronization. Run 30 full-dataset passes for descriptive batch throughput. Exactly one candidate invocation, followed only on exit 0 by one separate CPU-only raw auditor. No game, GUI, OS input, model/provider, Docker, training, or network in candidate/auditor.
- **D:** PASS only if all CPU/GPU output objects (including status, value and top two per-slot scores) are byte-equivalent after JSON parsing; source/input hashes and denominator are exact; independent auditor errors=0; all three frozen output/hash/timing mutations reject; and median CUDA single-frame latency <= 0.5× CPU median. Parity without speed is FAIL_GPU_NO_PRACTICAL_SPEEDUP. Mismatch is FAIL_CUDA_READER_MISMATCH. Integrity issues are HOLD_INTEGRITY. Any gate failure before invocation is STOP / NOT_EVALUATED.
- **C:** Windows 10 host, RTX 3080 Laptop GPU, CPython 3.11.9, PyTorch 2.5.1+cu121 / CUDA 12.1, Pillow 10.4.0; local thermal/clock and page-cache effects; 23 selected screenshots are a tiny fixed set. Pair order is alternating by repetition and frame index.
- **U:** This tests exact HUD state extraction, not threat recognition, beneficial action effect, action causality, closed-loop gameplay, survival, MAP01 exit, broad latency, or human tempo. It does not satisfy #59's live threat-exposure condition.

## Frozen invocation and resource boundary

Run preflight tests and then the corrected fail-closed gpu_preflight_gate.ps1. Require PREFLIGHT_OK; capture full stdout/stderr/status. Candidate output directory must be newly created and empty. Candidate command:
python gpu_hud_runner.py --dataset dataset.json --wad data/freedoom2.wad --out-dir results/t1-host-gpu-02
Audit command, only when candidate exit is 0:
python audit.py --raw results/t1-host-gpu-02/candidate_result.json --out results/t1-host-gpu-02/audit_result.json

Host-only local GPU allocation by the user's direct instruction: 04:05–04:20 UTC on 2026-10-01. No shared Docker/OrbStack resources. If the device is busy, inputs/source/hash changes, any start gate fails, or the slot expires, preserve STOP before candidate. No retry or result-driven modification.