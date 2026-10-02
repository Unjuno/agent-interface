# One-shot WSLc protocol — #6509 T0

- Runtime: Microsoft WSLc 3.0.1.0, cached pinned image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64).
- Use `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`; do not use Docker/Podman or GPU.
- Mount frozen source read-only, each run's input read-only as applicable, and unique host output directory writable. Keep created containers; no `--rm`.
- Before each rung, verify latest-main freeze, exact source/image hashes, fresh output path, no same-path/branch/PR collision, and no active shared WSLc owner. Do not infer a lease from an empty container snapshot. If another owner is active, perform no container invocation and retain a pre-run STOP.
- Order: one WSLc construction/test container; only on exit 0, one candidate container; only on exit 0 and renewed gates, one separate raw-only auditor container. No retries or source edits after freeze.
- Preserve full command, UTC times, exit codes, stdout/stderr, container IDs, raw SHA-256, audit output, runtime warnings, and exact invocation counts.
- This is a synthetic method gate only. It does not authorize live GUI, model, human, or external-effect tests.
