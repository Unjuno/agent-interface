# Allocation-06: transfer-inclusive CUDA break-even in a pinned container

This is a fresh successor allocation for Issue #5882. It does not alter allocation-03 HOLD_INTEGRITY, allocation-04 queue-collision STOP, or allocation-05 STOP_BEFORE_CANDIDATE_EXPIRED_WINDOW.

## Frozen experiment

- Allocation: GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-06
- Source base: main 0b8fcbd1ee8e1ac7c5ebfc137dcecd7226ea7477 at freeze
- Fresh seed: 49720261006; 1,024 typed synthetic rows, 256 per stratum
- Batch sizes: 1, 4, 16, 64, 256, 1,024; 5 warmups and 30 alternating paired repetitions
- Image: pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 (linux/amd64; cached locally)
- Runtime target: PyTorch 2.5.1+cu121, CUDA 12.1, RTX 3080 Laptop GPU passed through Docker Desktop desktop-linux
- Owner-bound interval: 2026-10-01 22:45-23:00 UTC; candidate once, then one CPU-only auditor container only if candidate exits 0; retries 0

The CUDA path includes host-list extraction, tensor construction, H2D, compute, synchronization, D2H, and CPU-owned final admission. The dataset is synthetic and fixed before measurement.

## H / T / D / C / U

See PREREGISTRATION.md for the frozen hypothesis, decision rule, controls, limits, and start/stop gate.

## Execution record

Prepared and CPU-preflighted only. Formal candidate/auditor outputs will be retained here after the reserved interval. The source and dataset are read-only mounted in the candidate container; only the unique output directory is writable. No image pull/build or network is allowed.
