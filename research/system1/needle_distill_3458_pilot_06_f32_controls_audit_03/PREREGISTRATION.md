# Issue #3906 — float32-tolerant invalid-control audit

Audit-only successor. Preserve #3899's STOP and output, #3892, merged PR #3882, #3869 and the original model FAIL unchanged.

## H — hypothesis

A wrapper that applies typed float32 tolerance to only the five serialized invalid-control feature vectors, and exact checks to their case/metadata/reason/proposal/NaN encoding, can compose with the frozen full covariate auditor to reproduce the retained result with zero audit errors. No IID-vs-shift equality is asserted. The model remains `FAIL_NEAR_BOUNDARY_SHIFT`.

## T — frozen treatment

- Allocation `needle-3869-covariate-audit-f32-controls-03`; immutable raw result from merge commit `f7d5cc8535995db0c36dd85d4b71877503bd0db8`, path `research/system1/needle_distill_3458_pilot_06_isolated_shift_audit/formal/formal-01/FORMAL_RESULT.json`, canonical SHA-256 `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`, Git blob `d6259323e86dba3ae12f76765aed62ab9d78dfa8`.
- Compose with predecessor `research/system1/needle_distill_3458_pilot_06_corrected_covariate_audit_02/audit.py`, pinned to #3899 commit `e978a33473d7d2536d43cf68ffcb16e344e4b6d8` and SHA-256 `a5a5a12cbebfe5891106c782f1ddb2bf96d32fea3bf3f598318e3881288d8fee`.
- Finite invalid-control values are compared with absolute tolerance `1e-6`; vector width, case, metadata, reason, proposal, and serialized `"NaN"` position remain exact. Only after each row passes is a deep-copy vector normalized to decimal literals for the predecessor's exact comparator. Original raw bytes are never modified and are passed through unchanged for SHA/blob verification.
- Construction controls accept representative float32 round-trips, reject mutation beyond tolerance, reject non-string NaN, and reject altered identity/decisions. All suite rows, six features, model-state hashes, proposals, metrics, shifted bounds, boundary controls, invalid controls, latency and gates are checked by the pinned predecessor.
- Freeze this wrapper/tests/environment/input/parent-source/image/command before exactly one local Docker formal audit. No training, inference, runner, GPU, network, or retry.

## D — decision

Audit PASS requires bound raw identities, zero wrapper or predecessor errors, 15/15 controls validated, all full-result checks passing, and unchanged numeric gates `[false,false,false]` / `FAIL_NEAR_BOUNDARY_SHIFT`. This is evidence-integrity PASS only and cannot convert the scientific model FAIL. Otherwise retain typed FAIL/STOP and do not retry.

## C — constraints

Use cached `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, linux/amd64, Python 3.12.14, torch 2.5.1+cpu, CPU only; network none, read-only repository/input, dedicated writable audit output, 2 CPUs, 4 GiB RAM, 64 pids, 64 MiB tmpfs. No pull/prune.

## U — limits

One posthoc evidence-integrity audit of a single synthetic three-seed experiment. No real-task alignment, task effect, runtime/product safety, execution authority, or generalization claims.
