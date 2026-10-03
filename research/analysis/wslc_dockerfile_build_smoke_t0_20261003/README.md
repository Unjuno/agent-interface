# WSLc Dockerfile build/run smoke T0

This is a deliberately tiny migration-capability check: build a local Dockerfile from an already-cached, digest-pinned Python base and run its deterministic entrypoint through WSLc without Docker Desktop or `docker.exe`.

It does not compare runtimes, measure iteration latency or peak memory, establish Docker feature parity, or validate any application workload. The WSLc `--memory` request is recorded only as a CLI parameter; this host has not demonstrated effective cgroup/swap enforcement.

See [FREEZE.md](FREEZE.md) for H/T/D/C/U, exact commands, no-retry limits, and frozen source hashes. Formal execution is pending the GitHub preregistration comment.

## Execution update — 2026-10-03

The initial sentence above records the pre-run staging state. The one frozen WSLc build and run later passed, and the separate offline receipt audit passed. See [RESULT.md](RESULT.md) and [AUDIT_RESULT.md](AUDIT_RESULT.md); neither result establishes runtime-speed or memory benefit.
