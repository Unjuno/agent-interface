# Issue #7475 T0 evidence package

Attempt 01 is retained in `attempt01_exploratory/` as a STOP because its answer key was not frozen before wording was drafted. It is not counted as a pass.

Attempt 02 is a three-pair synthetic card-equivalence audit. `facts.json` and `answer_key.json` were hash-locked in `PREWORDING_LOCK.json` before `stimuli.json` was created. Host execution and independent auditing report `PASS_METHOD_SCOPED` with all three negative controls rejected. The same candidate and independent auditor were replayed in WSLc using the cached Python image digest `sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, `--pull never`, no network, a read-only source bind, separate writable output bind, and CPU/memory limits. Outputs matched host execution; memory enforcement was not independently verified. A command template is included; the exact local mount path is redacted.

The experiment source context was Issue #7475 and main `0178fd24e9c317fff40e0fa1952fbe7e8ae01078`. The review branch is based on current main `fb49a59295093629997821159a1be2f7df6ef936`; the intervening main update is recorded only as delivery provenance.

This is stimulus-factor and answer-key consistency only. It provides no evidence about real user interpretation, approval, authorization, or control outcome. See `attempt02/README.md`, raw outputs, and SHA manifests.
