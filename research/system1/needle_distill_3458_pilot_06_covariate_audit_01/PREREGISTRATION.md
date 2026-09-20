# Issue #3892 — full six-covariate raw audit

Audit-only successor to merged PR #3882 and closed Issue #3869. Preserve every prior raw byte, FAIL, and auditor attempt unchanged.

## H — Hypothesis

An independent audit can reproduce the frozen three-seed evaluation from the retained generator seeds and model weights, including all six shifted-CORRECT input features. In particular, every shifted row will satisfy confidence `[0.80,1.00]` and `visible=1`, not only the position and velocity restrictions called out by the post-merge review.

## T — Frozen audit

- Immutable source result is from merge commit `f7d5cc8535995db0c36dd85d4b71877503bd0db8`, Git blob `d6259323e86dba3ae12f76765aed62ab9d78dfa8`, SHA-256 `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`.
- No model, training, seed, optimizer, or runner invocation. Regenerate the exact IID and shifted data arrays from the frozen Torch CPU seeds and source rules; check each raw six-dimensional vector and teacher label; check model state digest; independently reconstruct proposal/YIELD outputs from the serialized weights; recompute metrics, boundaries, five invalid cases, latency sample counts and p95.
- For each of six feature columns, a construction corruption control perturbs that column and must be rejected by the independent vector comparator. Include explicit confidence/visibility range controls.
- Before the single formal audit invocation, freeze source/test/image/result hashes, thresholds, command and output path. The formal audit runs once in local no-network Docker CPU; no retries.

## D — decision

`PASS_AUDIT_FULL_SHIFT_COVARIATES_SCOPED` requires exact normalized raw-result SHA-256 and Git-blob identity; all six features for all 3,072 rows in each suite independently regenerated within `1e-6`; confidence/visibility and every other declared bound satisfied; labels, model predictions, weights digest, gates, boundary and invalid controls reconstructed; the original `FAIL_NEAR_BOUNDARY_SHIFT` reproduced; all six feature corruption controls rejected; and zero audit errors. An evidence defect is a typed `HOLD_AUDIT_INPUT_OR_PROVENANCE`; predictive gate misses remain a scientific FAIL and cannot be upgraded by this audit.

## C / U

Use cached local Docker image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, CPU-only, network none, read-only root/source/input, separate writable audit output, 2 CPUs, 4 GiB memory, 64 pids, 64 MiB tmpfs. No GUI, external inference, network, GPU, retraining, runtime change, or action.

This is posthoc evidence integrity only for one synthetic experiment. It establishes no real-task intent fidelity, Astra labels, task effect, runtime safety, or generalization. Original PR #3882 and Issue #3869 remain immutable historical records.
