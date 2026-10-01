# Allocation-05 construction report

Status: preparation only; no candidate, CUDA kernel, or independent formal auditor invocation.

## Freeze

- Allocation: `GPU-HUD-CUDA-5752-20261001-05`.
- Preparation base: `b54ec8fac5d005d510a5787d98b9ad7a24d96923`, observed at 2026-10-01 09:53:52 UTC. Exact main must be refreshed and the source dependency closure rechecked at the reserved start.
- Branch/path: `research/gpu-hud-cuda-5752-20261001-05` / `research/doom/map01_hud_cuda_5752_t1_v5/`.
- Prior allocation-04 remains terminal `STOP_INSUFFICIENT_DISK_SPACE`, candidate=0; its ID, branch, STOP receipt, and history are not reused or modified.

## Construction checks

- `python -B -m unittest test_hud_failure_evidence -v`: 3/3 passed (frozen identity is dynamic; first parity mismatch atomically preserves a classified partial result; insufficient durable space stops before output).
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\gate_correction\test_gpu_preflight_gate.ps1`: 8/8 passed, zero failures.
- Before copying into this task-local additive scratch path, local source SHA-256 values matched the existing allocation-04 freeze for `gpu_hud_runner.py`, `audit.py`, `hud_independent.py`, and `dataset.json`. The exact retained input inventory was 23 PNGs (4,555,208 bytes) and a local Freedoom WAD of 28,787,748 bytes, SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
- Windows CPython 3.11.9, PyTorch 2.5.1+cu121 and one CUDA device are available. Readiness is not a scientific result. No CUDA computation was run during construction.
- Pre-formal review found the inherited preparation runner began its `gpu_cold_setup_ms` interval after CUDA template creation. Before any candidate, allocation-05 was corrected so the interval begins before first CUDA synchronization/template creation and includes the first decoded/scored frame; the preregistration now states exactly what it includes/excludes. No previous allocation result is changed.

## Formal boundary

The exclusive host RTX 3080 window is 2026-10-01 10:20–10:40 UTC. At start, refetch main and queue, verify exact source/input/WAD hashes, ensure at least 64 MiB free durable-output space, check for competing GPU processes and an empty unique output, and ensure the reserved slot remains clear. Then run the single frozen candidate; run the independent CPU-only auditor only if candidate exit is 0. Candidate/auditor/retry limits are 1/1/0. Any failed gate is STOP/NOT_EVALUATED; allocation-04 is never retried.

Scope is exact HUD parity and warm per-frame CUDA speed over 23 retained images only. No threat detection, causal effect, gameplay, MAP01 clearance, integrated #59 result, or broad GPU-performance claim follows.

