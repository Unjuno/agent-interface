# Issue #5730 — CPU-only launch-gate and artifact-publication construction

## H / T / D / C / U

**H.** A small host-only gate wrapper can guarantee that malformed or empty resource-inventory output, failed commands, incomplete source identity, candidate nonzero status, or absent/truncated artifact publication prevents scientific evaluation and is retained as a typed STOP; a successful simulated path is auditable byte-for-byte. This does not test GPU arithmetic or performance.

**T.** Freeze current `main` and this directory's exact source hashes before running the confirmatory matrix. In deterministic synthetic fixtures, exercise empty inventory output, failed inventory command, malformed/schema-invalid inventory, incomplete and changed source identity, candidate nonzero exit, absent output, truncated JSON, post-write digest mismatch, and a valid success. Verify the candidate callback count is zero for prerequisite failures. Run a separate standard-library-only auditor after the candidate matrix. No CUDA, GPU tensor, model, Docker, game, GUI, or input.

**D.** Every malformed/missing prerequisite yields nonzero-in-spirit STOP before candidate callback (`candidate_invocations=0`). Invalid/missing/truncated output yields `scientific_result=NOT_EVALUATED` and `raw_sha256=null`. Only complete JSON durably written and matching byte digest yields `ARTIFACT_PUBLISHED` and `READY_FOR_INDEPENDENT_AUDIT`. The independent auditor must reconstruct the frozen case outcomes from immutable raw JSON, validate source identity and artifact hashes, and reject mutated copies. The matrix demonstrates wrapper behavior only; it does not authorize a formal GPU allocation.

**C.** Host Python process semantics, the wrapper's own return/exception handling, local filesystem atomic-replace behavior, and synthetic byte fixtures. It does not test actual Windows GPU exclusivity, CUDA correctness, local device state, or scientific ROI performance.

**U.** A synthetic callback cannot establish production launcher correctness, shared-resource exclusivity, filesystem guarantees on every platform, or GPU behavior. Any later live diagnostic still requires a fresh #5085 award, source/image freeze, complete resource-owner identity and start gates. Do not rerun or rewrite the failed predecessor.

## Frozen run boundary

- Base: `main` at `5ff239141f49c1603c0f6b078268f4a2f6e082df` (read from GitHub API at start).
- Runtime: host CPython; standard library only.
- Candidate invocations: synthetic callbacks only; no device/resource probing.
- One confirmatory matrix invocation; then one independent auditor process. No retry.
- Exploratory unit-test invocation before this preregistration was finalized is non-confirmatory and excluded from the result.
