# Issue #7924 WSLc Dockerless local smoke A02 — first-run report

## Decision

**FAIL_AUDITOR_CONTRACT.** The candidate's scoped WSLc portability probe passed, but the allocation gate required an independent audit pass. The frozen auditor failed on its own field-name mismatch, so the overall gate did not pass. This is not evidence against WSLc runtime behavior.

## Candidate

- Exactly one candidate container invocation, exit 0, using WSLc 3.0.1.0 and `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` with `--pull never`, `--network none`, one CPU, requested 512M memory, read-only source bind, unique name, CID file, and `--rm`.
- Container Python: 3.12.14. Fixture hash matched `a534d2138b0a8fbb37c0930c54f8c9922acbd1dd8109d9abd69c8659271dc965`; attempted source write failed with errno 30 (`EROFS`). Candidate status: `PASS_PORTABILITY_SCOPED`.
- Exact candidate CID inspection after `--rm` reported the object absent. No global list was used.
- WSL emitted: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” Therefore 512M is only a requested setting; no hard-cap, swap-isolation, memory-relief, OOM, or peak-memory conclusion follows.

## Independent auditor

The frozen auditor ran exactly once in a second disposable WSLc container and exited 1 with `KeyError: 'sha256'`. `FREEZE.json` defines `source_sha256`, but three auditor expressions still look up `sha256`; execution stopped at the first such reference before the remaining assertions. No `AUDIT.json` was produced. The exact failure is retained in `AUDIT_ATTEMPT.json`. The exact auditor CID was inspected and reported absent after `--rm`.

A first targeted-inspect command for the auditor CID contained a transcription error; it is retained in `AUDITOR_CLEANUP.json` and was not used as cleanup evidence. A corrected inspect of the exact CID from `AUDITOR_CID.txt` confirmed absence. No unrelated container/image was inspected or changed.

## Scope and disposition

Docker calls, image pulls, global container-list calls, model calls, GUI calls, external network calls, game calls, and OS input calls: zero. Candidate and auditor were not rerun; frozen files were not edited. The completed probe supports only this host/image/read-only-bind normal-exit path. It does not establish Docker parity, speed benefit, memory-cap effectiveness, or broad migration readiness. A future successor should first freeze an auditor whose every lookup matches `source_sha256`, then independently validate the preserved A02 bytes without altering this first outcome.
