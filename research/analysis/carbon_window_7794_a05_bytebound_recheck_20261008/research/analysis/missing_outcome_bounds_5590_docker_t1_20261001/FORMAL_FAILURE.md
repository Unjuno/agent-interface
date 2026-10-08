# Docker T1 allocation STOP — output bind mount denied candidate write

## Disposition

`STOP_CONTAINER_OUTPUT_PERMISSION_DENIED_AFTER_CANDIDATE_INVOCATION`. This allocation produced no auditable scientific result. Do not interpret the process exit as `FAIL_INTEGRITY`: the candidate computed its in-memory result, then Docker denied persistence to the mounted output path. Candidate invocation count is **1** (exit 1); independent auditor invocation count is **0**. Allocation `MANSKI-SHARP-MISSING-OUTCOME-5590-GHA-T1-20261001-01` is consumed and must not be retried.

## Provenance and executed evidence

- Issue: https://github.com/Unjuno/agent-interface/issues/5590
- Pull request: https://github.com/Unjuno/agent-interface/pull/5642
- GitHub Actions run: https://github.com/Unjuno/agent-interface/actions/runs/36777588463 (head `c6d3140207dfa950c6ac5364992cae163635b490`; job `110099296877`).
- Container image reference: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; inspected image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, `linux/amd64`.
- Docker Engine 28.0.4 on GitHub-hosted Ubuntu 24.04; Python image runtime 3.12.14.
- Start gate passed: PR base and live main matched frozen `b92f2abb21e796150287135a74599fea64cc9759`; exact-head bounded source verification passed for all four payload files.
- Construction-test Docker invocation: exit 0, 8/8 tests passed.
- Candidate command: `python -B candidate.py ledger.json /out/raw.json`; Docker invocation exited 1. Exact stderr in `results/docker-t1-01/candidate.stderr.txt` is `PermissionError: [Errno 13] Permission denied: '/out/raw.json'`. Candidate stdout is empty and `raw.json` was not produced.
- The workflow correctly skipped the independent auditor because candidate did not exit 0. No retry, image rebuild, or second container invocation occurred.
- Exact uploaded Actions artifact ID `11126795229`; artifact ZIP SHA-256 `a5b216873b19b5046185ad90d2566c7c88d0da645f2b4e2ce4a2383270a54aad`. Downloaded logs and runtime receipts are retained below and listed in `results/docker-t1-01/SHA256SUMS.txt`.

## Cause and successor boundary

The process inside the container lacked permission to write into the host-owned bind mount despite the mount being configured writable. This is a container identity/volume-permission defect in the harness, not a bounds-method result. Any successor must have a fresh allocation and test output-mount writability during the construction gate before invoking the candidate; pass the host runner UID/GID explicitly or use another non-root mapped output strategy. Preserve this STOP unchanged and do not treat an unpersisted in-memory candidate value as raw evidence.
