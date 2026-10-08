# Formal report — Issue #3899

## Result

Audit status: **FAIL / auditor serialization-comparison overconstraint**. Scientific disposition independently recomputed from the immutable model result: **`FAIL_NEAR_BOUNDARY_SHIFT`**. Numeric gates by seed: `[false, false, false]`.

The one-shot audit bound the input bytes successfully (canonical SHA-256 `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7`; Git blob `d6259323e86dba3ae12f76765aed62ab9d78dfa8`). It reconstructed all 18,432 six-feature values per suite/seed, model-state digests, predictions, labels, metrics, shift bounds, boundary decisions and latency checks. It asserted no IID-to-shift feature equality.

The only 15 reported audit errors arise from the 5 invalid-control feature vectors per seed being compared against exact decimal literals. In the retained source these are float32 tensors serialized as Python floats: `0.2` appears as `0.20000000298023224`, `0.9` as `0.8999999761581421`, and `1.3` as `1.2999999523162842`. Case, metadata, proposal and YIELD reason checks pass. Thus the audit FAIL is not a predictive/model result; it also cannot certify audit PASS. Original model FAIL is unchanged.

## Invocation and integrity

Exactly one formal invocation; no retry, model training, model inference, or runner execution. Local Docker CPU image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, network disabled, source/input read-only, 2 CPU / 4 GiB / 64 pids / 64 MiB tmpfs. Nonfatal PyTorch warning: NumPy unavailable; the audit does not use NumPy.

`audit/formal-01/AUDIT.json` is 4,410 bytes; SHA-256 `135f1cb1f7175f92d2da3ac45c5c0ff5b1c8ba25289e6433d88958038364f29a`. Preserve it and the frozen source unchanged. Corrected float32-tolerant successor: Issue #3906.

## Per-seed shifted suite

| Seed | Accuracy | CORRECT accepted recall | Numeric gate |
|---:|---:|---:|:---:|
| 3467 | 0.741243 | 0.186683 | FAIL |
| 3468 | 0.701543 | 0.025799 | FAIL |
| 3469 | 0.783047 | 0.300606 | FAIL |

IID accuracy remains diagnostic and does not rescue any shifted-suite failure. This is synthetic-only evidence, not a real-task or execution-authority claim.
