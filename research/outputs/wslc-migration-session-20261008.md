# WSLc migration session status — 2026-10-08

## Outcome

The Dockerless local-route migration is already present on `main`: use native WSL for eligible work that does not require a container boundary, and use Microsoft's WSL Containers (`wslc`) for eligible single-container Linux-image workflows. Docker Desktop/Engine is not a prerequisite for those workflows. This record does not claim Docker parity, improved memory usage, or a general migration of every historical experiment.

## Current-session checks

- `wsl.exe --version`: WSL 3.0.1.0.
- `wslc.exe --version`: WSLc 3.0.1.0.
- `docker.exe`: not found on PATH.
- Read-only Windows process snapshot: 0 active `wslc.exe` clients at the observation instant.
- No WSLc inventory/run/build, Docker operation, candidate, auditor, memory-pressure test, process termination, or WSL restart was performed in this session.
- The configured top-level task folder is not a Git checkout. The available nested repo `repo-wslc-a04-current-main-20261008` is on `research/wslc-local-smoke-7924-a04-20261008-r3`, not a clean current-main checkout; this session made no source changes in it.

## Existing policy and evidence

Main's `.github/wslc-local-containers.md` already documents native WSL vs WSLc selection, scoped WSLc build/run, no-network/read-only-source guidance, and known cgroup/swap enforcement limits. It says not to launch Docker, restart shared WSL, change global WSL settings, or run memory pressure solely to use the local route. A WSLc smoke script uses a unique temporary path/container and an ID-scoped cleanup query. Existing PR #6114 and #7020 show narrow Dockerless operations, with #7020 specifically limited to a simple Dockerfile without RUN/package installation; its independent audit has a recorded qualification.

## Remaining separately gated work

- [#6389](https://github.com/Unjuno/agent-interface/issues/6389): native Ubuntu/WSL2 vs WSLc pilot; latest recorded disposition says shared runtime/source ownership remains unverified.
- [#6693](https://github.com/Unjuno/agent-interface/issues/6693): same-host Docker vs WSLc cost comparison; requires explicit lane release and a usable same-host Docker baseline. Docker is unavailable in this session.
- [#7430](https://github.com/Unjuno/agent-interface/issues/7430): non-pressure native WSL vs WSLc memory measurement; no inference from the present version/process snapshot.
- [#7970](https://github.com/Unjuno/agent-interface/issues/7970): post-GA filesystem placement successor; its latest comments explicitly bar further WSLc RPC/inventory until ownership/exclusive-lane reconciliation.
- [#8518](https://github.com/Unjuno/agent-interface/issues/8518): newly found WSL container API follow-up to #6693; inspect its exact scope before any future work.

A zero-client snapshot is not owner authorization and does not resolve the explicit coordination gates. No gate is represented here as cleared.

## Safe next steps

1. Continue to select native WSL or WSLc according to the documented per-workflow requirements; do not install Docker merely to satisfy old generic container-first wording.
2. For actual experimental work, use a verified clean current-main checkout and a unique additive branch/path; first check the controlling issue's latest owner-release and conflict gates.
3. If no eligible experiment remains without external release, limit activity to read-only repository/issue research. Do not stop peers, inspect global container state, or invoke WSLc management/RPC under the current hold.
4. Keep all historical Docker results, STOP/FAIL/HOLD records, and consumed allocations unchanged. Report only scoped outcomes supported by retained evidence.
