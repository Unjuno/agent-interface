# Issue #3899 — corrected full-covariate audit

Audit-only successor to #3892. Preserve all predecessor issues, merged PRs, source, formal bytes, and audit attempts unchanged. The prior audit's sole errors were an unpreregistered IID-versus-shift equality assertion for velocity/confidence. The frozen #3869 treatment explicitly changes those covariates; no cross-suite equality is part of this allocation.

## H — hypothesis

Using the immutable #3869 result and its frozen source contract, an independent CPU auditor can regenerate all six features and labels per suite/seed, check the shifted CORRECT bounds including confidence and visibility, reproduce predictions and metrics, and confirm that the model's three-seed disposition remains `FAIL_NEAR_BOUNDARY_SHIFT`, with no evidence errors.

## T — frozen treatment

- Allocation `needle-3869-covariate-audit-corrected-02`; seeds 3467, 3468, 3469 inherited only as immutable input metadata; no generation for a new model and no training/inference runner.
- Input from merge commit `f7d5cc8535995db0c36dd85d4b71877503bd0db8`, `research/system1/needle_distill_3458_pilot_06_isolated_shift_audit/formal/formal-01/FORMAL_RESULT.json`; expected SHA-256 `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`, Git blob `d6259323e86dba3ae12f76765aed62ab9d78dfa8`.
- Independently regenerate each suite/seed with the frozen Torch generator. Compare every 6-float row, label, model digest, proposal and YIELD reason; recompute per-seed metrics and numeric gates from audited rows. Never compare IID feature values to shifted values for equality.
- Explicitly validate all 1,024 shifted CORRECT rows/seed: `abs(dx)` in `[.071,.149]`, `abs(dy)<=.10`, `abs(vx),abs(vy)<=.05`, confidence `[.80,1.00]`, visible `1`.
- Test each feature-column mutation independently, plus deterministic regeneration and suite-specific velocity/confidence differences. Recompute all 1,536 explicit boundary decisions, five invalid-control outcomes, and the 2,000-sample CPU latency integrity/p95 gate; none can upgrade the model's failed shifted-suite gates.
- Freeze source, tests, environment, input hash, image ID and one-shot Docker command before the sole formal audit invocation. No retry or model execution.

## D — decision

`PASS_AUDIT_FULL_SHIFT_COVARIATES_SCOPED` iff exact raw SHA-256 and Git-blob identity bind; all 6 features and labels regenerate for both 3,072-row suites per seed within `1e-6`; model-state digests and every stored decision reproduce; all shifted-CORRECT bounds/visibility hold; all three shifted-suite numeric gates recompute as false and disposition remains `FAIL_NEAR_BOUNDARY_SHIFT`; six corruption tests reject their mutations; and auditor errors are empty. Any missing/bad evidence is `FAIL`/`HOLD` for this audit; never convert the scientific FAIL to PASS.

## C — constraints

Local Docker only, cached `needle-pilot05:local`, exact image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14, torch 2.5.1+cpu, CPU-only, network none, read-only root/source/input, isolated writable output, 2 CPUs, 4 GiB RAM, 64 pids, 64 MiB tmpfs. Do not pull/prune images, use GPU, train, or rerun.

## U — limits

Posthoc evidence-integrity audit of one synthetic three-seed experiment only; no real labels, Astra intent, task effects, runtime/product safety, authority, or generalization claims.
