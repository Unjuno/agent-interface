# Preregistration — Issue #4853

H/T/D/C/U and seed allocation are in GitHub Issue #4853. This pins executable details before the one formal run.

- Allocation `needle-role-c-support64-diagnostic-4749-v4-seed7866401`; exactly one formal orchestration, no retry.
- Same #4749 upstream runner, base data/400-update training, shared initial adapter, optimizer, C minibatch seed+12 and 120 update steps. Control uses the first 16 rows; treatment uses 64. A/B are paired invariants.
- Before fitting, verify the upstream Git blob, seed and empty output mount. Regenerate 64 and 16 examples with `seed+3`; require shape/dtype equality, `torch.equal`, and equality of flattened contiguous uint8 bytes. Test byte serialization with a sentinel and run a corrupted-prefix rejection control. The entire construction test has zero optimizer updates.
- Retain every role's held-out inputs, expected labels, predictions and model tensors for both C arms. Independent auditor reconstructs predictions/labels, role scores, A/B parity and exact signed C delta without importing the trainer or paired runner.
- Report a single-seed descriptive outcome. No #4749 multi-seed threshold is applied; no one-point inference about the distribution or external validity.
- Cached local Docker image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10`, Linux/amd64, CPU only, offline, read-only root/source, 1 CPU, 2 GiB, 64 PIDs and dedicated output volume. No GUI, network, GPU, real user data or actuator.

