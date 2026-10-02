# Issue #5590 Docker T1 — bounded finite-cohort result reproduction

## Lineage and question

This is a fresh, additive container-portability rung for the already-executed host T0 in `missing_outcome_bounds_5590_t0_20261001/`. It does not retry or inherit the consumed OrbStack STOP allocation `MANSKI-SHARP-MISSING-OUTCOME-5590-DOCKER-20261001-01`; it uses a new GitHub-hosted Linux runner and isolated Docker invocations. The candidate, auditor, ledger and tests are byte-identical to the prior T0 sources. The scientific estimand and synthetic example are unchanged.

## H / T / D / C / U

- **H:** The frozen finite-cohort bounds candidate and independent auditor execute reproducibly in a digest-pinned Linux container with network-disabled candidate/auditor processes, preserving the host T0 exact result and all declared integrity rejections.
- **T:** At PR-open, require current GitHub `main`, PR base, and this package's frozen main SHA to agree. Retrieve only the four manifest-listed files at the exact PR head using bounded host-side HTTPS; verify freeze, manifest and each file hash before execution. Pull one pinned Python image. Run one construction-test container, then one candidate container; only if candidate exits zero run one separate raw-only auditor container. Candidate and auditor containers use `--network none`, read-only root/source/input, separate writable output, 1 CPU, 256 MiB, 64 PIDs, dropped capabilities and no-new-privileges. No retries.
- **D:** `PASS_BOUNDS_SCOPED_DOCKER_REPRODUCTION` only if source/image/main gates pass, tests pass, candidate and raw-only auditor each exit 0, audit status is `PASS_BOUNDS_SCOPED`, counts remain `N=10,S=6,F=1,M=3`, bounds remain `[3/5,9/10]` around threshold `3/4`, all 8 completions are present, and all five integrity mutations remain rejected. Any scientific mismatch is `FAIL_INTEGRITY`; source/main/image/container/provenance inability is `STOP`, not scientific failure.
- **C:** This reproduces the deterministic host T0 finite-cohort arithmetic in a container. It does not validate a real benchmark cohort or replace its terminal-outcome oracle.
- **U:** Synthetic finite-cohort arithmetic only; no sampling uncertainty, missingness model, population generalization, scorer validity, real task effect, runtime safety, or benchmark-promotion claim.

## Frozen identities

- Allocation: `MANSKI-SHARP-MISSING-OUTCOME-5590-GHA-T1-20261001-01`.
- Frozen current main at preparation: `818ebd32a52a74acf26724e4f00739d19d9ecdbf`.
- Predecessor host T0: `090f523009f93d79b8bf0d58e269ae0b7f688703`; retained unchanged in PR #5627 and its source hashes.
- Container image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, expected `linux/amd64`.
- Package files and hashes are frozen in `FREEZE.json` and `SHA256SUMS.txt`.

## Execution boundary

The PR-open workflow is the only formal invocation path. A start-gate mismatch consumes this allocation as STOP; it is never silently retried. Preserve exact commands, image/runtime identity, standard streams, exit codes, raw result, independent audit, and hashes under `results/docker-t1-01/`. Host construction checks and remote Actions status are supporting workflow evidence, not substitutes for the executed Docker candidate/auditor.
