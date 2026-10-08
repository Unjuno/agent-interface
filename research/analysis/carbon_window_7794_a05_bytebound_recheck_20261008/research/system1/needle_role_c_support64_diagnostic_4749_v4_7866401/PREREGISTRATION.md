# Preregistration — Issue #4853

H/T/D/C/U and seed allocation were recorded on the GitHub Issue before the sole formal run.

- One paired support16/control and support64/treatment; seed 7866401. Same frozen #4749 runner and base data/training (400 updates), shared adapter initialization, optimizer/minibatch stream and 120 updates per B/C; first 16 support rows are the exact prefix of 64.
- Before fitting, verify runner Git blob, allocation, empty output; regenerate support data and assert shape, dtype, torch.equal and flattened contiguous uint8-byte equality. Sentinel serialization and corrupted-prefix rejection are construction checks with zero optimizer updates.
- Retain all held-out role inputs, expected labels, predictions and model tensors. Independent raw-only auditor reconstructs labels/predictions, role scores, A/B parity and signed C delta without importing trainer or paired runner.
- Exactly one formal invocation, no retry/substitution. One seed is descriptive only; no #4749 multi-seed threshold inference.
- Pinned local CPU Docker image; network none, read-only root/source, 1 CPU, 2 GiB, 64 PIDs and dedicated output volume. No GUI, GPU, user data or actuator.
