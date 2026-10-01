# Allocation-08: WSL Podman transfer-inclusive CUDA break-even

Fresh successor to #5882 allocation-06, which terminally stopped before candidate launch. Allocation-07 is a separate pending Docker Desktop request; neither predecessor is modified or reused.

## Frozen experiment

- Allocation: GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-08
- Main base at registration: 093b39fdab8d8cd04c422f8d9956deef1b40a692
- Fresh seed: 49720261008; 1,024 typed synthetic rows, 256 in each of four strata
- Batch sizes: 1, 4, 16, 64, 256, 1,024; 5 warmups and 30 alternating pairs
- Container: Podman rootful/crun in Arch Linux WSL 2 with NVIDIA CDI
- Image: pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 (linux/amd64)
- Proposed interval: 2026-10-02 00:45–01:00 UTC; request only until queue/owner release checks pass

The CUDA route times host-list extraction, tensor construction, H2D, compute, synchronization, D2H, and CPU-owned final admission. No candidate or auditor has run for allocation-08.


## Terminal disposition update — 2026-10-01 UTC

Allocation-08 stopped before candidate launch with `STOP_PRE_CANDIDATE_NO_GRANTED_NONOVERLAPPING_GPU_WINDOW`. Candidate/CUDA/fit/auditor/retry counts are 0/0/0/0/0. See [STOP_REPORT.md](STOP_REPORT.md). The original 00:45–01:00 UTC interval was request-only and overlapped another same-device request. No scientific result is claimed.
