# Formal report — Issue #3906

## Result

Evidence-integrity audit: **PASS**. Scientific disposition: **`FAIL_NEAR_BOUNDARY_SHIFT`**; numeric gates `[false, false, false]`. This is not a model PASS.

The audit bound the unchanged result (canonical SHA-256 `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`, Git blob `d6259323e86dba3ae12f76765aed62ab9d78dfa8`), reconstructed all six features and labels for IID and shifted suites across three seeds (18,432 feature values per suite/seed), recomputed model-state hashes, decisions and metrics, checked shifted CORRECT bounds including confidence and visibility, boundary decisions, all 15 invalid controls and latency evidence. There were zero audit errors and no cross-suite feature-equality assertion.

The float32-aware layer exactly checked case, metadata, proposal/reason, vector width and serialized `"NaN"`; finite scalars were compared within the preregistered `1e-6` tolerance. Only after those checks did it normalize an in-memory deep copy for the frozen predecessor auditor. The raw input bytes were unchanged and identity-bound.

## Per-seed shifted suite

| Seed | Accepted accuracy | CORRECT accepted recall | Numeric gate |
|---:|---:|---:|:---:|
| 3467 | 0.741243 | 0.186683 | FAIL |
| 3468 | 0.701543 | 0.025799 | FAIL |
| 3469 | 0.783047 | 0.300606 | FAIL |

IID results do not rescue the shifted-suite failures. All evidence remains synthetic and authority-neutral.

## Invocation and integrity

Exactly one formal local Docker audit invocation; no model runner, training, inference, GPU or network. Image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, CPU-only, limits 2 CPU / 4 GiB / 64 pids / 64 MiB tmpfs, read-only repo and dedicated writable output. A nonfatal PyTorch warning reported NumPy is unavailable; no NumPy-dependent operation was used.

`audit/formal-01/AUDIT.json`: 3,993 bytes, SHA-256 `6f9bcf7d2f079302ca73a10fa1c1618afaaedef1f175f1dda23199503a41a4a6`. No retries are permitted or needed.
