# Preserved first outcome — allocation 01

The source/fixture were frozen and read back byte-identically from the GitHub branch before execution. Candidate ran once in the pinned local Docker container and exited 0, emitting 6,453 bytes. The independent auditor ran once and exited 1 with five metric mismatches.

Read-only diagnosis: candidate's generic `duplicate_effects = len(effects)-1` counted two sequential effects separated by fresh feedback as duplicates in the no-integrator control. The auditor also incorrectly used the stale-generation-effect count as the duplicate count for old-generation queued actions. Therefore allocation 01 is `FAIL_CONSTRUCTION_METRIC_CONTRACT_MISMATCH`; it does not decide the anti-windup hypothesis. No retry or source edit was made. Candidate stdout/raw, audit traceback, exit receipts, frozen source/fixture and hashes are retained unchanged.

Environment: Docker Desktop 29.8.0 linux/amd64; `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, network none, 1 CPU, 256 MiB, pids 64. Both containers used `--rm`; no container remains.

