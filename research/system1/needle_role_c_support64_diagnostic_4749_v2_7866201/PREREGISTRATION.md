# Preregistration — Issue #4848

H/T/D/C/U are frozen in GitHub Issue #4848. This file pins executable detail before fitting.

- Allocation: `needle-role-c-support64-diagnostic-4749-v2-seed7866201`; exactly one paired seed and no resampling.
- Control uses `xc64[:16]`; treatment uses all `xc64`. Both begin from the exact same trained A base and adapter initialization; C uses the same `seed+12` minibatch stream for 120 AdamW updates. Base uses 400 updates; B is an invariant control.
- Prefix: independently call public `upstream_runner.data(16, seed+3)` and compare dimensions, dtype, exact values and serialized raw bytes with `xc64[:16]`; gate before first training operation.
- Record every heldout input, expected label, prediction and tensor state for A/B/C in both arms. Independent auditor reconstructs predictions directly from serialized tensors and recomputes labels/accuracy; it imports no runner or paired wrapper.
- No thresholds borrowed from #4749 are applied to a single-seed diagnostic. Report signed accuracy delta, audit disposition, and all controls. A technical failure is STOP/HOLD, not evidence about the effect.
- Environment: pinned local CPU image in README; offline, read-only source/root, 1 CPU, 2 GiB, 64 PIDs, dedicated output volume. No network/GPU/live app/user data.
- Formal invocation may occur once after issue/source/image/commands are read back from GitHub. Keep any setup/preflight failure chronology. No retry, hyperparameter change or substitution.

