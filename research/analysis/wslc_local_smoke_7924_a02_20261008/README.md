# Issue #7924 — WSLc Dockerless local smoke A02

## H / T / D / C / U

- **H:** With no active WSLc client at the preflight snapshot and a clean current-main checkout, one uniquely named, disposable, offline WSLc Python container can read a hash-bound Windows-host fixture from a read-only bind and receives `EROFS` on a write attempt.
- **T:** Freeze the exact main SHA, image digest, fixture, candidate, auditor, unique candidate/auditor names, and commands. Run candidate once using `--pull never --network none --cpus 1 --memory 512M --rm`, a read-only source bind and a unique name/CID file. Independently verify saved stdout and frozen hashes. Use only name/ID-targeted post-run inspection; no global container inventory and no Docker operation.
- **D:** `PASS_PORTABILITY_SCOPED` only if candidate exit is 0, fixture hash matches, write fails specifically with `EROFS`, frozen image/runtime/command are retained, targeted inspection shows the unique `--rm` container absent, and independent audit passes. First failure is final; no retry. This is not a speed, hard-memory-cap, memory-relief, Docker-parity, or general migration claim.
- **C:** WSLc service can still change between process snapshot and run; `--memory` may not be enforced as a hard cap; C-drive bind performance differs from WSL filesystem; no network-exclusion adversarial test is performed.
- **U:** One host, one Python image, and one simple CPU process only. No GUI, Docker daemon/API/Compose, build behavior, abnormal-exit cleanup, OOM protection, peak-memory, or broad workload qualification.

## Provenance and stop boundary

This is a new A02 after the prior #7924 readiness STOP, not a rerun of an earlier smoke. The local source snapshot is a clean sparse worktree at the exact current-main SHA in `FREEZE.json`; the existing dirty checkout and all older WSLc objects remain untouched. Active `wslc.exe` process count was zero at the preflight snapshot. Stopped container/image ownership remains unknown, so no global inventory, prune, stop, or cleanup is permitted.

The container receives only the package directory mounted read-only at `/src`; `--rm` is scoped to the uniquely named candidate/auditor container. CID files and result bytes are retained in this package. Requested memory settings are recorded as configuration only, not as proof of an effective cap.

## Result

Result: **FAIL_AUDITOR_CONTRACT**. The single candidate invocation passed the scoped read-only/offline WSLc probe; exact fixture SHA matched and a source write failed with EROFS. The independent auditor invocation failed with `KeyError: 'sha256'` because its frozen code expects a field absent from FREEZE.json (`source_sha256`). The allocation gate therefore did not pass; no `AUDIT.json` was produced. Both unique containers were confirmed absent by exact-CID inspection after `--rm`. The WSL cgroup/swap warning means the requested 512M is not a proven effective limit. See `REPORT.md`, `RUN_RECEIPT.json`, and `AUDIT_ATTEMPT.json`. No retry or frozen-source edit occurred.
