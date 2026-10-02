# T0 report — Issue #5850

**Status:** `PASS_METHOD_SCOPED` (synthetic method experiment only).
**Allocation:** `5850-ASSAY-SENSITIVITY-T0-20261001-01`.

The frozen synthetic fixture tests eight claim-card states. Local construction tests passed 4/4. A host candidate invocation and separately implemented raw-only oracle agreed on all eight rows; the oracle rejected 8/8 declared summary mutations. Fixture SHA-256: `88c5366bcb83349c2d7ecedf91bdade9fc91a6a8fe8a8129761f6bd811e0c735`. See [construction result](results/construction-01/RESULT.json).

## Formal isolated-container result

GitHub Actions run [36834347134](https://github.com/Unjuno/agent-interface/actions/runs/36834347134) ran the frozen source at `0a9341cca27722cfea639859ea488b6ddec51b89`. The candidate and auditor each ran once in distinct containers and both exited 0. Docker Engine was 28.0.4 on Linux amd64; image was `python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`). Candidate container ID: `404a3e61311057f18bd6a9348037878486333cb924c70345ddf583175e10f4de`; auditor container ID: `7064f05d4b0e0b0929a43da8a0a670d166097ba2847238f93242c13b0ddb2444`. Both used `network=none`, read-only root, 128 MiB, 1 CPU, 32 pids, no-new-privileges and dropped all capabilities; neither OOM-killed.

The auditor reconstructed all eight expected dispositions, matched the candidate's exact row map and frozen fixture digest, and rejected all 8/8 declared mutations. Raw candidate output SHA-256: `fbabdaa92562f991c32da6ca86298b1d084d7eefbcc0d3fe5d225cf4743111fe`; the original workflow checksum manifest was independently verified against Git blob bytes. See the retained [formal output](results/5850-ASSAY-SENSITIVITY-T0-20261001-01/), [post-run audit](results/5850-ASSAY-SENSITIVITY-T0-20261001-01/POST_RUN_AUDIT.json), and supplemental integrity hashes.

## Scope

This is a deterministic synthetic method result, not evidence about any live #57 route, real measurement noise, candidate benefit, equivalence, speed, tokens, cost, or adoption. The null disposition explicitly means interpretable as a null under the synthetic card, not equivalence. The host Desktop daemon was unresponsive; formal Docker execution therefore used the isolated GitHub-hosted engine above. No retry or second allocation occurred.
