# Issue #4463 formal STOP

Disposition: `STOP_CUDA_DETERMINISTIC_OPERATOR_UNAVAILABLE`.

The frozen local host-GPU runner was invoked exactly once on 2026-09-26 JST with `CUBLAS_WORKSPACE_CONFIG=:4096:8`, deterministic algorithms enabled, and the RTX 3080/CUDA 12.1 environment. It reached the first CNN backward call, then PyTorch raised:

`adaptive_avg_pool2d_backward_cuda does not have a deterministic implementation`

No `results.json` was produced, so no training comparison, evaluation, PASS/FAIL/HOLD scientific result, or independent audit exists. The exact runner log is retained as `results/formal01/runner.log` with SHA-256 `68d53c1b6e0b30d7ff838d2c32663997e1d3b384e21f39d697e15da359df2def` and 1,567 bytes. The allocation is consumed; no retry, nondeterministic fallback, operator substitution, threshold change, or tuning was performed.

This is a host-GPU infrastructure/protocol STOP, not evidence that brightness augmentation succeeds or fails. Earlier #3682/#3693/#3694 outcomes remain unchanged.
