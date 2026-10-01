# Allocation-05 transfer-inclusive GPU break-even probe

This is a fresh successor allocation for Issue #5882. Allocation-03's HOLD_INTEGRITY and the withdrawn allocation-04 STOP remain unchanged.

## Frozen package

- Allocation: GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261001-05
- Base main at source freeze: c427c704404fc2b35ea9e06a57e61d239b77b369
- Seed: 49720261005; 1,024 newly generated synthetic rows
- Runner: transfer-inclusive CPU/CUDA comparison at 1, 4, 16, 64, 256 and 1,024 rows
- Corrected auditor: unsafe-admission negative control flips a guaranteed zero, with a fail-closed error when no zero exists
- Assigned GPU window: 2026-10-01 11:30–11:40 UTC, exact queue record #5085 comment #5929212100

At preparation time, the exact branch sources were read back from GitHub and checked locally: source/dataset SHA-256 values match FREEZE.json; Python compile passed; contract tests 3/3; mutation-control tests 3/3; full synthetic raw-auditor baseline 0 errors and corruption controls 5/5. No GPU candidate or timing run has occurred.

## Start gate

At 11:30 UTC, refresh current main and the complete #5085 queue, verify the owner-bound exact interval, current runtime/device, source/data/freeze hashes, output path absence, process/GPU inventory and at least 1 GiB free C: space stable across two readings 60 seconds apart. If main changed since FREEZE.json, synchronize the additive branch and update only the base-main/time fields, then reverify all source/data hashes. Any failed or ambiguous gate means STOP before candidate. No retry.

The formal candidate and independent auditor outputs will be added here only after the bounded allocation.