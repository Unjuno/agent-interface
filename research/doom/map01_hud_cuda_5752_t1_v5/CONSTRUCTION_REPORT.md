# Allocation-05 construction report

Status: formal allocation-05 completed; candidate=1, independent auditor=1, retry=0.

## Freeze

- Allocation: `GPU-HUD-CUDA-5752-20261001-05`.
- Preparation base: `b54ec8fac5d005d510a5787d98b9ad7a24d96923`, observed at 2026-10-01 09:53:52 UTC. Start-gate main: `c427c704404fc2b35ea9e06a57e61d239b77b369`, observed at 2026-10-01 10:20:54 UTC; comparison showed 0 changes to the pinned Doom HUD source/input paths.
- Branch/path: `research/gpu-hud-cuda-5752-20261001-05` / `research/doom/map01_hud_cuda_5752_t1_v5/`.
- Prior allocation-04 remains terminal `STOP_INSUFFICIENT_DISK_SPACE`, candidate=0; its ID, branch, STOP receipt, and history are not reused or modified.

## Construction checks

- `python -B -m unittest test_hud_failure_evidence -v`: 3/3 passed (frozen identity is dynamic; first parity mismatch atomically preserves a classified partial result; insufficient durable space stops before output).
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\gate_correction\test_gpu_preflight_gate.ps1`: 8/8 passed, zero failures.
- Before copying into this task-local additive scratch path, local source SHA-256 values matched the existing allocation-04 freeze for `gpu_hud_runner.py`, `audit.py`, `hud_independent.py`, and `dataset.json`. The exact retained input inventory was 23 PNGs (4,555,208 bytes) and a local Freedoom WAD of 28,787,748 bytes, SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Windows CPython 3.11.9, PyTorch 2.5.1+cu121 and one CUDA device are available. Readiness is not a scientific result. No CUDA computation was run during construction.
- Pre-formal review found the inherited preparation runner began its `gpu_cold_setup_ms` interval after CUDA template creation. Before any candidate, allocation-05 was corrected so the interval begins before first CUDA synchronization/template creation and includes the first decoded/scored frame; the preregistration now states exactly what it includes/excludes. No previous allocation result is changed.

## Formal boundary

The exclusive host RTX 3080 window was 2026-10-01 10:20–10:40 UTC. Start-gate main and queue were refreshed; comparison found no changed pinned HUD inputs/source paths. The output path was absent, C: had >5 GiB free, CUDA reported 0 MiB / 0%, and the compute-process table was empty. CPU construction tests passed 3/3; start gate exited 0; exact 23 PNG/RGB, four report/event, WAD, runner and reference hashes all matched. Candidate ran once, 10:23:42.991–10:25:08.894 UTC, exit 0; independent CPU auditor ran once, 10:25:24.296–10:25:30.260 UTC, exit 0. The active CUDA process was observed using 207 MiB at 3% and later 347 MiB; no retry occurred. Raw evidence and detailed outcome are in `results/t1-host-gpu-05/` and `RESULT.md`. Allocation-04 is never retried.

Outcome: `PASS_CUDA_HUD_EQUIVALENCE_SPEED_SCOPED`; exact CPU/CUDA parity on all 23 frames and both signals; 690 paired timing observations; CPU p50 37.33115 ms, CUDA p50 15.91615 ms, median ratio 0.42635 (2.35× speedup). Independent audit errors=0; all three mutation controls rejected. A PyTorch warning about the read-only NumPy array was emitted; it did not cause a candidate failure and is preserved in the console log. No claim beyond the preregistered narrow method scope follows.

Scope is exact HUD parity and warm per-frame CUDA speed over 23 retained images only. No threat detection, causal effect, gameplay, MAP01 clearance, integrated #59 result, or broad GPU-performance claim follows.

