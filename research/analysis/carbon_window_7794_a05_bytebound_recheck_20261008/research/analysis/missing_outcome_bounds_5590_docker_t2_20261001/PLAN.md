# Issue #5590 Docker T2 — Obstac output-mount construction and bounds reproduction

## Lineage and question

Fresh successor to host-only T0 and consumed Docker T1. T1 remains unchanged: its candidate was invoked once but could not persist `/out/raw.json`; no raw result or auditor run exists. T2 asks whether a frozen, writable bind-mount preflight under an explicit runner UID/GID permits a separately invoked candidate and independent auditor to persist and verify the exact same synthetic finite-cohort result. T2 does not change the scientific question, ledger, candidate, auditor, or tests.

## H / T / D / C / U

- **H:** With an immutable Obstac allocation, pinned image, frozen source closure, and explicit UID/GID, the construction gate can prove the dedicated output mount writable before any candidate invocation; the one candidate result can then be independently checked from raw bytes.
- **T:** Locally run the construction test suite, candidate, independent raw-only audit, and five integrity mutations in a pinned Docker image with network disabled and read-only source/input. The formal allocation additionally checks current-main/base/freeze identity and exact source hashes, then runs a write/read/delete probe as the first container gate. Only a successful probe and construction suite permit exactly one candidate invocation; only a persisted candidate output permits exactly one independent auditor invocation. No retries.
- **D:** `PASS_BOUNDS_SCOPED_DOCKER_REPRODUCTION` requires all provenance gates, writable-mount probe, 8/8 construction tests, candidate and auditor exit 0, audit status `PASS_BOUNDS_SCOPED`, N=10/S=6/F=1/M=3, threshold 3/4, sharp interval [3/5,9/10], all 8 completions, and all five mutations rejected. Scientific mismatch is `FAIL_INTEGRITY`; inability to establish a technical/provenance gate is `STOP`. A failed mount probe means candidate=0 and auditor=0.
- **C:** Reproduction of deterministic synthetic finite-cohort arithmetic and the container output transport boundary.
- **U:** No real benchmark cohort, sampling uncertainty, missingness model, population generalization, scorer validity, real task effect, runtime safety, or promotion claim.

## Frozen identities and execution policy

- Allocation: `MANSKI-SHARP-MISSING-OUTCOME-5590-GHA-T2-20261001-01`.
- Freeze commit is the exact current `main` SHA recorded in `FREEZE.json`; formal start requires live main = PR base = frozen SHA.
- T1 predecessor: allocation `MANSKI-SHARP-MISSING-OUTCOME-5590-GHA-T1-20261001-01`, preserved STOP in the T1 package on main.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/amd64`).
- Network none; read-only root and source/input; only a dedicated output bind mount is writable; 1 CPU, 256 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. Docker processes use the runner's numeric UID:GID. Output probe must succeed in the construction invocation before tests complete.
- Source inventory and SHA-256 values are frozen in `FREEZE.json` and `SHA256SUMS.txt`.

## Obstac evidence boundary

The immutable freeze and source manifest precede formal execution. Preserve exact invocation receipts, mount-probe output, image/runtime identity, stdout/stderr, exit codes, raw result, independent audit, and hashes under `results/docker-t2-01/`. Local host/unit checks are development evidence only; formal container evidence is the one-shot allocation. Any failed formal gate consumes T2 as a STOP or FAIL according to the predicate; do not rerun it. A new attempt requires a separately preregistered successor allocation.
