# Issue #5590 — Docker T2 Obstac output-mount reproduction

## Disposition

`PASS_BOUNDS_SCOPED_DOCKER_REPRODUCTION`. One fresh formal allocation completed without retry. The output-mount defect observed in T1 did not recur with the construction-stage write/read/delete probe and numeric runner UID:GID. The frozen synthetic bounds result matched the preregistered predicate, and a separate raw-only auditor passed.

This is a deterministic synthetic finite-cohort arithmetic reproduction only. It does not establish a real benchmark cohort's promotion status, a population effect, scorer validity, missingness assumptions, task benefit, or product safety. The parent Issue #5590 remains open for real-cohort design and evidence.

## H / T / D / C / U

- **H:** With an immutable Obstac allocation, pinned image, source closure, and explicit UID/GID, the output mount can be proven writable before candidate invocation; the persisted candidate output can be independently checked from raw bytes.
- **T:** The PR-open workflow checked current main = PR base = frozen main, fetched only four bounded source files from the exact PR head, verified freeze/manifest/source hashes, pulled the pinned image, ran one writable-mount probe before construction tests, then invoked the candidate once and a separate raw-only auditor once. No retries.
- **D:** All frozen gates passed. The audit reported `PASS_BOUNDS_SCOPED`, errors empty, N=10/S=6/F=1/M=3, sharp bounds `[3/5,9/10]`, threshold 3/4, and 8 compatible completions. All 8 construction tests passed, including the five integrity mutations. Mount probe, construction, candidate, and auditor exit codes were all 0.
- **C:** Reproduction of the exact deterministic synthetic ledger's finite-cohort arithmetic and the Docker output-bind-mount boundary on one GitHub-hosted Linux/amd64 Docker runner.
- **U:** No real benchmark cohort, population generalization, sampling uncertainty, missingness model, scorer validity, real task effect, or promotion recommendation.

## Formal execution provenance

- Issue: https://github.com/Unjuno/agent-interface/issues/5590
- PR: https://github.com/Unjuno/agent-interface/pull/5643
- Allocation: `MANSKI-SHARP-MISSING-OUTCOME-5590-GHA-T2-20261001-01`.
- Run: https://github.com/Unjuno/agent-interface/actions/runs/36780361039; job `110108780113`; head `3d95b99daef88b81dfca6eaad27377749761cef5`.
- Start-gate JSON records frozen main and PR base `c68b5e6778e9b82ee2c21e9709f35aa253bf1613`, exact head, four files, and `PASS_PREFLIGHT`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; inspected image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, linux/amd64.
- Runner: GitHub-hosted Linux x86_64, Docker Engine 28.0.4; numeric UID:GID 1001:1001. The container Python patch version was not emitted by the frozen workflow and is intentionally not inferred.
- Output mount probe: wrote, read, and deleted a sentinel; exit 0. The construction container then passed 8/8 tests. Candidate invocation count 1, exit 0, wrote `/out/raw.json`; independent auditor invocation count 1, exit 0.
- Raw SHA-256: `0f428c7d3da7b29cb982d1d7502536c3f562e569d6e16d18e4e7d37f5e1ed4ec`.
- Audit SHA-256: `00cd1f13ba775126aecbab7cc90ac8adf8f1dd062c8a11c7bcf44277095e5e6c`.
- GitHub artifact ID `11127099488`, name `issue-5590-docker-t2-36780361039`; downloaded ZIP SHA-256 `d0a847b22d95ca160f50c46c698a1713952513ad8dcf6997bcc5796700054f02`. Exact ZIP and extracted runtime files are retained in `results/docker-t2-01/` with `SHA256SUMS.txt`.
- Formal raw bytes are identical to the earlier host-only development raw. The formal result stands on the actual container execution and separate container auditor, not on that host run.

## Local development evidence and predecessor

Local host tests, candidate, independent audit, mutation controls, and repository CI passed before the formal allocation; these are separately documented in [LOCAL_VALIDATION.md](LOCAL_VALIDATION.md) and `results/local-development-01/`. The local OrbStack daemon was not available, so no local container invocation is claimed. T1's prior `STOP_CONTAINER_OUTPUT_PERMISSION_DENIED_AFTER_CANDIDATE_INVOCATION` remains unchanged in the predecessor package; T2 is a new allocation and does not overwrite that STOP.

## Reproduction and retained evidence

The exact formal `preflight.json`, image/runtime identity, Docker version, mount-probe output, construction stdout/stderr, exit codes, candidate raw/stdout/stderr, independent audit, artifact index and original artifact ZIP are retained under `results/docker-t2-01/`. Verify them by running `cd results/docker-t2-01 && shasum -a 256 -c SHA256SUMS.txt` from this experiment directory. The one-shot Actions run is not to be rerun; further questions require a separately preregistered successor allocation.
