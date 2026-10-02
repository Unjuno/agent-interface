# Frozen WSLc run protocol — Issue #6519 T0

Runtime: Microsoft WSL Containers CLI `wslc.exe` 3.0.1.0; cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/amd64`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`). Do not pull, use Docker/Podman, or use GPU.

For every invocation use `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`; retain containers (no `--rm`); freeze source mounts read-only and give each stage a unique writable output directory. Preserve WSLc's memory/swap warning verbatim and do not claim the configured memory limit was enforced.

1. Construction exactly once, with package root mounted read-only at `/src`, workdir `/src`, unique construction output at `/out`:

   `python -B -m unittest -v test_protocol`

2. Only after construction exits 0 and all gates remain clear, candidate exactly once. Mount `formal_01_20261002/candidate_source` read-only at `/src`; mount the fresh candidate output at `/out`:

   `python -B /src/candidate.py /src/fixture.json /out/candidate.raw.json`

   Candidate source intentionally excludes `oracle.json` and `auditor.py`.

3. Only after candidate exits 0 and all gates are rechecked, auditor exactly once. Mount `formal_01_20261002/audit_source` read-only at `/src`, the byte-identical copied candidate raw at `/in/candidate.raw.json` read-only, and a fresh audit output at `/out`:

   `python -B /src/auditor.py /src/fixture.json /src/oracle.json /in/candidate.raw.json /out/audit.json`

No retries. Any nonzero exit, protocol mismatch, source/hash drift, concurrent owner, or fresh-gate failure stops all later rungs. Every command is run with separate stdout/stderr and exit receipts; preserve all outputs and IDs.
